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


def update_client_configuration():
    try:
        data = request.json  # Receiving form data

        client_id = data.get("client_id")  # Correcting the field name
        icp_job_seniorities = data.get("icp_job_seniorities", [])

        if not client_id:
            return jsonify({"success": False, "message": "Missing required field: client_id"}), 400

        # Ensure icp_job_seniorities is a comma-separated string
        if isinstance(icp_job_seniorities, list):
            icp_job_seniorities = ", ".join(icp_job_seniorities)

        # Prepare the Airtable payload
        airtable_data = {
            "records": [
                {
                    "fields": {
                        "client_id": client_id,  # Matching Airtable field names
                        "icp_job_seniorities": icp_job_seniorities  # Now a string
                    }
                }
            ]
        }

        # Send to Airtable
        response = requests.post(AIRTABLE_URL, json=airtable_data, headers=HEADERS)

        if response.status_code in [200, 201]:
            return jsonify({"success": True, "message": "Data saved successfully", "response": response.json()}), 201
        else:
            return jsonify({"success": False, "message": "Failed to save data", "error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
