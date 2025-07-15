from flask import Flask, jsonify
import requests
import traceback
import ast
import os
import time
import pickle
import tempfile

from airtable import Airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, APIFY_API_TOKEN, OPENAI_API_KEY

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import openai
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# Airtable setup
TABLE_NAME = "influencers_instagram"
instagram_airtable = Airtable(AIRTABLE_BASE_ID, TABLE_NAME, AIRTABLE_API_KEY)

# Google Drive setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.pickle')
SCOPES = ['https://www.googleapis.com/auth/drive.file']


# === Authenticate Google Drive ===
def get_authenticated_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build("drive", "v3", credentials=creds)


def upload_to_drive(image_url):
    tmp_path = None
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        if response.status_code != 200:
            print(f"⚠️ Failed to download image: {image_url}")
            return None

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", mode='wb') as tmp_file:
            for chunk in response.iter_content(1024):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        del tmp_file

        drive_service = get_authenticated_drive_service()
        file_metadata = {"name": os.path.basename(tmp_path)}
        media = MediaFileUpload(tmp_path, mimetype="image/jpeg", resumable=False)

        uploaded = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        file_id = uploaded.get('id')

        drive_service.permissions().create(
            fileId=file_id, body={"role": "reader", "type": "anyone"}
        ).execute()

        del media  # Release file handle before deleting temp file
        os.remove(tmp_path)

        return f"https://drive.google.com/uc?id={file_id}&export=download"

    except Exception as e:
        print(f"❌ Error uploading to Drive: {e}")
        traceback.print_exc()

        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as cleanup_err:
                print(f"⚠️ Cleanup error: {cleanup_err}")

        return None


import traceback

def analyze_image_with_gpt(image_url):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
Analyze the image and generate image tags for the given image. Return ONLY a JSON object like:

{"tags": ["coffee", "beach", "phone"]}

Rules:
- Include actions, objects, clothing, and locations useful for influencer marketing.
- No explanation. Just the JSON.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=200,
            temperature=0.5,
        )

        content = response.choices[0].message.content.strip()
        return eval(content)

    except Exception as e:
        print(f"❌ Vision GPT error: {e}")
        traceback.print_exc()
        return {"tags": []}



# === Apify Scraper ===
def get_image_urls_from_apify(post_url):
    try:
        payload = {"url": post_url}
        headers = {'Content-Type': 'application/json'}
        run_response = requests.post(
            f"https://api.apify.com/v2/acts/pratikdani~instagram-posts-scraper/runs?token={APIFY_API_TOKEN}",
            json=payload,
            headers=headers
        )
        run_response.raise_for_status()
        run_data = run_response.json()
        run_id = run_data.get("data", {}).get("id")

        if not run_id:
            return []

        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"
        max_wait_time, poll_interval, elapsed = 60, 5, 0

        while elapsed < max_wait_time:
            status_response = requests.get(status_url)
            status_data = status_response.json().get("data", {})
            status = status_data.get("status")

            if status == "SUCCEEDED":
                dataset_id = status_data.get("defaultDatasetId")
                break
            elif status in {"FAILED", "TIMED-OUT", "ABORTED"}:
                return []
            else:
                time.sleep(poll_interval)
                elapsed += poll_interval
        else:
            return []

        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
        items = requests.get(dataset_url).json()

        image_urls = []
        if isinstance(items, list) and items:
            for media_item in items[0].get("post_content", []):
                if media_item.get("type") == "Photo" and media_item.get("url"):
                    image_urls.append(media_item["url"])
                    break

        return image_urls
    except Exception as e:
        print(f"❌ Error scraping Apify: {e}")
        traceback.print_exc()
        return []


def extract_images():
    try:
        filter_formula = "AND(NOT({email_id} = ''), OR({influencer_location} = 'KSA', {influencer_location} = 'Saudi Arabia'))"
        records = instagram_airtable.get_all(filterByFormula=filter_formula)

        print(f"📦 Fetched {len(records)} records")

        for idx, record in enumerate(records):
            record_id = record.get('id')
            fields = record.get('fields', {})
            post_urls = fields.get('instagram_post_urls', [])

            if isinstance(post_urls, str):
                try:
                    post_urls = ast.literal_eval(post_urls)
                except:
                    post_urls = []

            print(f"\n📄 Processing Record {idx+1} — ID: {record_id}")
            print(f"🔗 Post URLs: {post_urls}")

            all_drive_urls = []
            all_tags = []

            for post_url in post_urls:
                image_urls = get_image_urls_from_apify(post_url)

                if image_urls:
                    image_url = image_urls[0]
                    print(f"🖼️ Scraped image: {image_url}")
                    drive_url = upload_to_drive(image_url)

                    if drive_url:
                        tags_json = analyze_image_with_gpt(drive_url)
                        tags = tags_json.get("tags", [])
                        all_drive_urls.append(drive_url)
                        all_tags.extend(tags)
                        print(f"✅ Uploaded to Drive: {drive_url}")
                        print(f"🏷️ Tags: {tags}")
                    else:
                        print("⚠️ Drive upload failed.")
                else:
                    print("⚠️ No image found.")

            if all_drive_urls or all_tags:
                try:
                    instagram_airtable.update(record_id, {
                        'instagram_post_image_urls': "\n".join(all_drive_urls),  # joined as long text
                        'image_tags': ", ".join(sorted(set(all_tags)))  # unique + sorted tags
                    })
                    print(f"📝 Airtable updated for record {record_id}")
                except Exception as airtable_err:
                    print(f"❌ Error updating Airtable: {airtable_err}")

        return {"status": "success", "message": "All records processed."}
    except Exception as e:
        print("❌ Error in processing:")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    app.run(debug=True)
