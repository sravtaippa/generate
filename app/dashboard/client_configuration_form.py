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

@app.route("/update_client_configuration_form", methods=["GET"])
def update_client_configuration():
    try:
        client_id = request.args.get("client_id")
        icp_job_seniorities = request.args.get("icp_job_seniorities", "")
        icp_job_details = request.args.get("icp_job_details", "")
        icp_locations = request.args.get("icp_locations", "")
        organization_domains = request.args.get("organization_domains", "")

        if not client_id:
            return jsonify({"success": False, "message": "Missing required field: client_id"}), 400

        def format_list_string(value):
            """Converts a comma-separated string into a properly formatted list string."""
            return str([s.strip() for s in value.split(",") if s.strip()])

        # Convert fields to properly formatted list strings
        icp_job_seniorities_str = format_list_string(icp_job_seniorities)
        icp_job_details_str = format_list_string(icp_job_details)
        icp_locations_str = format_list_string(icp_locations)
        organization_domains_str = format_list_string(organization_domains)

        # Find existing record ID
        record_id = find_record_by_client_id(client_id)

        airtable_data = {
            "records": [
                {
                    "fields": {
                        "client_id": client_id,
                        "icp_job_seniorities": icp_job_seniorities_str,
                        "icp_job_details": icp_job_details_str,
                        "icp_locations": icp_locations_str,
                        "organization_domains": organization_domains_str
                    }
                }
            ]
        }

        if record_id:
            airtable_data["records"][0]["id"] = record_id
            response = requests.patch(AIRTABLE_URL, json=airtable_data, headers=HEADERS)
        else:
            response = requests.post(AIRTABLE_URL, json=airtable_data, headers=HEADERS)

        if response.status_code in [200, 201]:
            return jsonify({"success": True, "message": "Data saved successfully", "response": response.json()}), response.status_code
        else:
            return jsonify({"success": False, "message": "Failed to save data", "error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"success": False, "message": "Internal Server Error", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
