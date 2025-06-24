from flask import Flask, request, jsonify
from pyairtable import Api
import requests
import json
import traceback
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, APIFY_API_TOKEN

AIRTABLE_TABLE_NAME = 'src_influencer_data'

# Airtable setup
api = Api(AIRTABLE_API_KEY)
airtable = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Apify Clockworks Scraper
CLOCKWORKS_URL = f"https://api.apify.com/v2/acts/clockworks~tiktok-profile-scraper/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"

app = Flask(__name__)
def scrape_and_store(username):
    try:
        payload = {
            "profiles": [username],
            "resultsPerPage": 5,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadSubtitles": False,
            "shouldDownloadVideos": False
        }
        print("Payload sent to Apify:", payload)
        response = requests.post(CLOCKWORKS_URL, json=payload)
        if response.status_code not in (200, 201):
            return {"status": "failed", "error": f"Apify error: {response.text}"}

        posts = response.json()
        print("Number of posts received:", len(posts))
        if not posts or not isinstance(posts, list):
            return {"status": "failed", "error": "No posts returned or data not a list"}

        recent_posts = posts[:5]  # Just in case, always slice to 5

        tiktok_share_count = [p.get('shareCount', 0) for p in recent_posts]
        tiktok_play_count = [p.get('playCount', 0) for p in recent_posts]
        tiktok_comment_count = [p.get('commentCount', 0) for p in recent_posts]
        tiktok_digg_count = [p.get('diggCount', 0) for p in recent_posts]
        tiktok_text = [p.get('text', '') for p in recent_posts]
        tiktok_video_urls = [p.get('webVideoUrl', '') for p in recent_posts]

        airtable_data = {
            "tiktok_username": username,
            "tiktok_share_count": json.dumps(tiktok_share_count),
            "tiktok_play_count": json.dumps(tiktok_play_count),
            "tiktok_comment_count": json.dumps(tiktok_comment_count),
            "tiktok_digg_count": json.dumps(tiktok_digg_count),
            "tiktok_text": json.dumps(tiktok_text),
            "tiktok_video_urls": json.dumps(tiktok_video_urls)
        }

        # Search for existing record
        existing = airtable.all(formula=f"{{tiktok_username}}='{username}'")
        if existing:
            record_id = existing[0]['id']
            record = airtable.update(record_id, airtable_data)
            action = "updated"
        else:
            record = airtable.create(airtable_data)
            action = "created"

        print(f"Airtable {action} response for {username}:", record, flush=True)

        return {
            "status": "passed",
            "message": f"TikTok posts data {action} successfully",
            "data": airtable_data
        }

    except Exception as e:
        print(f"Unexpected error for {username}:", e, flush=True)
        traceback.print_exc()
        return {"status": "failed", "error": f"Unexpected error: {str(e)}"}


if __name__ == '__main__':
    app.run(debug=True)
