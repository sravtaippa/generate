from flask import Flask, request, jsonify
import requests
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

app = Flask(__name__)

AIRTABLE_TABLE_NAME = "brand_influencer_brief_docs"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def submit_to_airtable(data):
    # Extract fields
    brand_id = data.get("brand_id")
    documents = data.get("documents", [])  # Should be a list of URLs

    # Prepare documents for Airtable (array of dicts with 'url' keys)
    airtable_documents = [{"url": url} for url in documents]

    # Prepare payload
    airtable_data = {
        "fields": {
            "brand_id": brand_id,
            "documents": airtable_documents
        }
    }

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(AIRTABLE_URL, headers=headers, json=airtable_data)

    if response.status_code in (200, 201):
        return {"status": "passed", "airtable_response": response.json()}
    else:
        return {"status": "failed", "error": response.text}



if __name__ == '__main__':
    app.run(debug=True)
