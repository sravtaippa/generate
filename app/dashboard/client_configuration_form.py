import requests   
from flask import Flask, request, jsonify

app = Flask(__name__)

# Airtable API details
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
BASE_ID = "app5s8zl7DsUaDmtx"
TABLE_NAME = "client_config"

AIRTABLE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def find_record_by_client_id(client_id):
    """Fetch the record ID for a given client_id."""
    params = {"filterByFormula": f"client_id='{client_id}'"}
    response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        records = response.json().get("records", [])
        if records:
            return records[0]["id"]  # Return first matched record ID
    return None

def update_client_configuration():
    try:
        client_id = request.args.get("client_id")
        icp_job_seniorities = request.args.get("icp_job_seniorities", "")

        if not client_id:
            return jsonify({"success": False, "message": "Missing required field: client_id"}), 400

        # Convert comma-separated values to a formatted string: "['Manager', 'Director', 'Executive']"
        icp_job_seniorities_list = [s.strip() for s in icp_job_seniorities.split(",") if s.strip()]
        icp_job_seniorities_str = str(icp_job_seniorities_list)  # Convert list to string format

        # Find existing record ID
        record_id = find_record_by_client_id(client_id)

        if record_id:
            # Update existing record
            airtable_data = {
                "records": [
                    {
                        "id": record_id,
                        "fields": {
                            "icp_job_seniorities": icp_job_seniorities_str  # Store as a formatted string
                        }
                    }
                ]
            }
            response = requests.patch(AIRTABLE_URL, json=airtable_data, headers=HEADERS)
        else:
            # Create new record
            airtable_data = {
                "records": [
                    {
                        "fields": {
                            "client_id": client_id,
                            "icp_job_seniorities": icp_job_seniorities_str  # Store as a formatted string
                        }
                    }
                ]
            }
            response = requests.post(AIRTABLE_URL, json=airtable_data, headers=HEADERS)

        if response.status_code in [200, 201]:
            return jsonify({"success": True, "message": "Data saved successfully", "response": response.json()}), response.status_code
        else:
            return jsonify({"success": False, "message": "Failed to save data", "error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
