import os
import pickle
import json
import tempfile
import requests
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
PICKLE_DIR = os.path.dirname(__file__)
TOKEN_PATH = os.path.join(PICKLE_DIR, 'token.pickle')
CREDENTIALS_PATH = os.path.join(PICKLE_DIR, 'credentials.json')

AIRTABLE_TABLE_NAME = "brand_influencer_brief_docs"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"


def get_authenticated_drive_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token missing or invalid. Please upload a valid token.pickle.")
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)


def upload_file_to_drive(file_obj, drive_service):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file_obj.save(tmp.name)
        file_metadata = {"name": file_obj.filename}
        media = MediaFileUpload(tmp.name, resumable=True)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

    file_id = uploaded_file.get("id")

    # Make file public
    drive_service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    # Direct download link
    file_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    return file_url


def submit_to_airtable(brand_id, file_urls):
    payload = {
        "fields": {
            "brand_id": brand_id,
            "documents": [{"url": url} for url in file_urls]
        }
    }
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post(AIRTABLE_URL, headers=headers, json=payload)
    return res.status_code, res.json()


@app.route('/submit_influencer_form', methods=['POST'])
def submit_influencer_form(brand_id, files):
    try:
        
        if not brand_id or not files:
            return jsonify({"status": "failed", "message": "Missing brand_id or files"}), 400

        drive_service = get_authenticated_drive_service()

        # Upload all files to Drive and collect their URLs
        file_urls = [upload_file_to_drive(f, drive_service) for f in files]

        # Send to Airtable
        status, airtable_response = submit_to_airtable(brand_id, file_urls)

        if status not in (200, 201):
            return jsonify({"status": "failed", "airtable_error": airtable_response}), 400

        return jsonify({
            "status": "success",
            "uploaded_files": file_urls,
            "airtable_response": airtable_response
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "failed", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
