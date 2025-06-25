import re
from flask import jsonify, request
from db.db_ops import db_manager 

# === Apify config ===
APIFY_TOKEN = "apify_api_OzlpdlQM48B0bXW6gKThLiVYz5nIcS35jGvl"
APIFY_API_URL = f"https://api.apify.com/v2/acts/tuningsearch~cheap-google-search-results-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"


# === Extract username from URL for Instagram or TikTok ===
def extract_username(url):
    if "instagram.com" in url:
        match = re.search(r"instagram\.com/([^/?#]+)", url)
    elif "tiktok.com" in url:
        match = re.search(r"tiktok\.com/@([^/?#]+)", url)
    else:
        return None
    return match.group(1) if match else None

# === Check for duplicates in PostgreSQL ===
def is_duplicate(media, username):
    if media.lower() == "instagram":
        field_name = "instagram_username"
    elif media.lower() == "tiktok":
        field_name = "tiktok_username"
    else:
        print(f"⚠️ Unknown media type for duplicate check: {media}")
        return False, username  # still return username for consistency

    exists = db_manager.unique_key_check(field_name, username, "influencers")
    return exists, username

# === Add new record to PostgreSQL with appropriate field names ===
def add_to_psql(media, username, url, influencer_type, influencer_location):
    fields = {
        "influencer_type": influencer_type,
        "influencer_location": influencer_location
    }
    if media.lower() == "instagram":
        fields["instagram_username"] = username
        fields["instagram_url"] = url
        fields["social_media_type"] = "instagram"
    elif media.lower() == "tiktok":
        fields["tiktok_username"] = username
        fields["tiktok_url"] = url
        fields["social_media_type"] = "tiktok"
    else:
        print(f"⚠️ Unknown media type: {media}")
        return

    db_manager.insert_data("influencers", fields)
    print(f"✅ Added to PostgreSQL: {username} ({media})")

# === Process scraped results and upload to PostgreSQL ===
def process_and_upload(results, media, influencer_type, influencer_location):
    seen = set()
    for item in results:
        url = item.get("url", "")
        username = extract_username(url)

        if username and username not in seen:
            seen.add(username)
            is_dup, extracted_username = is_duplicate(media, username)
            if not is_dup:
                add_to_psql(media, extracted_username, url, influencer_type, influencer_location)
            else:
                print(f"🔁 Skipped duplicate: {extracted_username}")
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

    import requests  # Only needed for Apify API
    response = requests.post(APIFY_API_URL, json=payload)

    if response.ok:
        results = response.json()
        print(f"Scraped Url: {results}")
        process_and_upload(results, media, influencer_type, influencer_location)
        return jsonify({
            "message": "Scraping complete, data uploaded to PostgreSQL",
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
