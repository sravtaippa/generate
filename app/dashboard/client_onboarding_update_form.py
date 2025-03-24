import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_BASE_ID = "app5s8zl7DsUaDmtx"
AIRTABLE_TABLE_NAME = "client_info"
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_record_id(client_id):
    """Fetches record_id from Airtable based on client_id."""
    response = requests.get(AIRTABLE_URL, headers=HEADERS)
    if response.status_code == 200:
        records = response.json().get("records", [])
        for record in records:
            if record["fields"].get("client_id") == client_id:
                return record["id"]
    return None

@app.route("/update_client_onboarding", methods=["POST", "GET"])
def update_client_onboarding():
    try:
        # Handle GET & POST Requests
        if request.method == "GET":
            client_id = request.args.get("client_id")
            full_name = request.args.get("full_name")
            email = request.args.get("email")
            job_title = request.args.get("job_title")
        else:  # POST request
            data = request.json if request.is_json else request.form
            client_id = data.get("client_id")
            full_name = data.get("full_name")
            email = data.get("email")
            job_title = data.get("job_title")

        # Debugging: Print received data
        print(f"Received Data: client_id={client_id}, full_name={full_name}, email={email}, job_title={job_title}")

        # Check for missing fields
        missing_fields = [field for field in ["client_id", "full_name", "email", "job_title"] if not locals()[field]]
        if missing_fields:
            return jsonify({"error": "Missing required fields", "missing": missing_fields}), 400

        # Get Airtable record_id
        record_id = get_record_id(client_id)
        if not record_id:
            return jsonify({"error": "Client not found in Airtable"}), 404

        # Prepare update data
        update_data = {"fields": {"full_name": full_name, "email": email, "job_title": job_title}}
        response = requests.patch(f"{AIRTABLE_URL}/{record_id}", json=update_data, headers=HEADERS)

        return jsonify(response.json()), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
