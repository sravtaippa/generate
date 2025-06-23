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

def extract_username(url):
    match = re.search(r"instagram\.com/([^/?#]+)", url)
    return match.group(1) if match else None

def add_to_airtable(username, url, influencer_type, influencer_location):
    data = {
        "fields": {
            "instagram_username": username,
            "instagram_url": url,
            "influencer_type": influencer_type,
            "influencer_location": influencer_location
        }
    }
    response = requests.post(AIRTABLE_URL, headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        print(f"✅ Added to Airtable: {username}")
    else:
        print(f"❌ Failed to add {username}: {response.text}")

def process_and_upload(results, influencer_type, influencer_location):
    seen = set()
    for item in results:
        url = item.get("url", "")
        username = extract_username(url)
        if username and username not in seen:
            seen.add(username)
            add_to_airtable(username, url, influencer_type, influencer_location)

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
        process_and_upload(results, influencer_type, influencer_location)
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
