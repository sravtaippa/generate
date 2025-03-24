from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Airtable API Configuration
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
BASE_ID = "app5s8zl7DsUaDmtx"
TABLE_NAME = "client_info"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_record_id(client_id):
    """Check if client_id exists in Airtable and return its record ID."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    params = {"filterByFormula": f"{{client_id}}='{client_id}'"}
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        records = response.json().get("records", [])
        if records:
            return records[0]["id"]  # Return existing record ID
    return None  # Client ID not found

def update_airtable_record(record_id, data):
    """Update an existing Airtable record."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    
    update_payload = {
        "records": [
            {
                "id": record_id,
                "fields": data
            }
        ]
    }
    
    response = requests.patch(url, headers=HEADERS, json=update_payload)
    return response.json()

def create_airtable_record(data):
    """Create a new Airtable record."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    
    create_payload = {
        "records": [
            {
                "fields": data
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=create_payload)
    return response.json()

@app.route('/update_airtable', methods=['POST'])
def handle_webhook():
    """Webhook endpoint to receive data from Bit Integration and update Airtable."""
    try:
        form_data = request.json
        client_id = form_data.get("client_id")  # Get client_id from Bit Integration
        
        if not client_id:
            return jsonify({"error": "Missing client_id"}), 400

        # Prepare Airtable fields
        airtable_data = {
            "email": form_data.get("email", ""),
            "full_name": form_data.get("name", ""),
            "job_title": form_data.get("job_title", ""),
            "location": form_data.get("location", ""),
            "phone": form_data.get("phone", ""),
            "company_name": form_data.get("company", ""),
            "company_website": form_data.get("website", ""),
            "instantly_campaign_id": form_data.get("instantly_campaign_id", "")
        }

        # Check if record exists
        record_id = get_record_id(client_id)

        if record_id:
            # Update record
            update_response = update_airtable_record(record_id, airtable_data)
            return jsonify({"status": "updated", "data": update_response}), 200
        else:
            # Create new record
            create_response = create_airtable_record(airtable_data)
            return jsonify({"status": "created", "data": create_response}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

