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
        # Get URL parameters
        client_id = request.args.get("client_id")  # Retrieve the 'client_id' from URL parameters
        icp_job_seniorities = request.args.get("icp_job_seniorities")  # Retrieve 'icp_job_seniorities'

        if not client_id or not icp_job_seniorities:
            return jsonify({"message": "Missing required parameters", "success": False}), 400

        # Process the data
        icp_job_seniorities = icp_job_seniorities.split(",")  # If you want to process as a list

        # Return success
        return jsonify({
            "client_id": client_id,
            "icp_job_seniorities": icp_job_seniorities,
            "success": True
        }), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}", "success": False}), 500


if __name__ == "__main__":
    app.run(debug=True)
