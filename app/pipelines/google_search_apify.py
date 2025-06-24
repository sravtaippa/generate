import requests
import re
from flask import jsonify, request

# === Apify config ===
APIFY_TOKEN = "apify_api_OzlpdlQM48B0bXW6gKThLiVYz5nIcS35jGvl"
APIFY_API_URL = f"https://api.apify.com/v2/acts/tuningsearch~cheap-google-search-results-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

# === Airtable config ===
AIRTABLE_BASE_ID = 'app5s8zl7DsUaDmtx'
AIRTABLE_TABLE_NAME = 'influencers'
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# === Extract username from URL for Instagram or TikTok ===
def extract_username(url):
    if "instagram.com" in url:
        match = re.search(r"instagram\.com/([^/?#]+)", url)
    elif "tiktok.com" in url:
        match = re.search(r"tiktok\.com/@([^/?#]+)", url)
    else:
        return None
    return match.group(1) if match else None

# === Check for duplicates based on media type ===
def is_duplicate(media, username):
    if media.lower() == "instagram":
        field_name = "instagram_username"
    elif media.lower() == "tiktok":
        field_name = "tiktok_username"
    else:
        print(f"⚠️ Unknown media type for duplicate check: {media}")
        return False

    filter_formula = f"{{{field_name}}} = '{username}'"
    params = {"filterByFormula": filter_formula}

    response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        records = response.json().get("records", [])
        return len(records) > 0
    else:
        print(f"⚠️ Error checking duplicate for {username}: {response.text}")
        return False

# === Add new record to Airtable with appropriate field names ===
def add_to_airtable(media, username, url, influencer_type, influencer_location):
    fields = {
        "influencer_type": influencer_type,
        "influencer_location": influencer_location
    }

    if media.lower() == "instagram":
        fields["instagram_username"] = username
        fields["instagram_url"] = url
    elif media.lower() == "tiktok":
        fields["tiktok_username"] = username
        fields["tiktok_url"] = url
    else:
        print(f"⚠️ Unknown media type: {media}")
        return

    data = {"fields": fields}

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        print(f"✅ Added to Airtable: {username} ({media})")
    else:
        print(f"❌ Failed to add {username}: {response.text}")

# === Process scraped results and upload to Airtable ===
def process_and_upload(results, media, influencer_type, influencer_location):
    seen = set()
    for item in results:
        url = item.get("url", "")
        username = extract_username(url)

        if username and username not in seen:
            seen.add(username)
            if not is_duplicate(media, username):
                add_to_airtable(media, username, url, influencer_type, influencer_location)
            else:
                print(f"🔁 Skipped duplicate: {username}")
        else:
            print(f"⚠️ Invalid or already seen username: {username}")

# === Flask route function to trigger scraping ===
def scrape_influencers(data, media, influencer_type, influencer_location, page):
    if not (media and influencer_type and influencer_location):
        return jsonify({"error": "Missing required params"}), 400

    if request.method == 'GET':
        search_query = f"{media} {influencer_type} in {influencer_location}"
    else:
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400
        search_query = data.get("query")
        if not search_query:
            return jsonify({"error": "Missing 'query' in request body"}), 400

    print(f"📡 Triggering Apify scrape: {search_query} | Page {page}")

    payload = {
        "language": "en",
        "query": search_query,
        "page": page
    }

    response = requests.post(APIFY_API_URL, json=payload)

    if response.ok:
        results = response.json()
        process_and_upload(results, media, influencer_type, influencer_location)
        return jsonify({
            "message": "Scraping complete, data uploaded to Airtable",
            "query": search_query,
            "page": page,
            "results_count": len(results)
        }), 200
    else:
        return jsonify({
            "error": "Apify API error",
            "status": response.status_code,
            "details": response.text
        }), 500
