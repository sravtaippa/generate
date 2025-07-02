import requests
import re
import uuid
import datetime
from flask import jsonify, request

# === Apify config ===
APIFY_TOKEN = "apify_api_OzlpdlQM48B0bXW6gKThLiVYz5nIcS35jGvl"
APIFY_API_URL = f"https://api.apify.com/v2/acts/tuningsearch~cheap-google-search-results-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"

# === Airtable config ===
AIRTABLE_BASE_ID = 'app5s8zl7DsUaDmtx'
AIRTABLE_TABLE_NAME = 'influencer_profile_urls'
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

# === Extract username from URL for Instagram or TikTok ===
def extract_username(url):
    if "instagram.com" in url:
        if "/reel/" in url or "/reels/" in url:
            return None
        match = re.search(r"instagram\.com/([^/?#]+)", url)
    elif "tiktok.com" in url:
        match = re.search(r"tiktok\.com/@([^/?#]+)", url)
    else:
        return None
    return match.group(1) if match else None

# === Check for duplicate using unique_profile_key ===
def is_duplicate(media, unique_profile_key):
    filter_formula = f"{{unique_profile_key}} = '{unique_profile_key}'"
    params = {"filterByFormula": filter_formula}
    response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        records = response.json().get("records", [])
        return len(records) > 0
    else:
        print(f"⚠️ Error checking duplicate for {unique_profile_key}: {response.text}")
        return False

# === Add new record to Airtable ===
def add_to_airtable(media, username, url, influencer_type, influencer_location):
    if not username:
        return

    unique_key = f"{media.lower()}_{username}"

    fields = {
        "id": str(uuid.uuid4()),
        "username": username,
        "social_media_type": media.lower(),
        "profile_url": url,
        "unique_profile_key": unique_key,
        "influencer_type": influencer_type,
        "influencer_location": influencer_location,
        "created_time": datetime.datetime.utcnow().isoformat()
    }

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
            unique_key = f"{media.lower()}_{username}"
            is_dup = is_duplicate(media, unique_key)
            if not is_dup:
                add_to_airtable(media, username, url, influencer_type, influencer_location)
            else:
                print(f"🔁 Skipped duplicate: {unique_key}")
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
        print(f"Scraped Url: {results}")
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
