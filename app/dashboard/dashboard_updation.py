from flask import Flask, jsonify
import requests
import logging
import re

# ✅ Configure logging
logging.basicConfig(level=logging.INFO)

# ✅ Airtable Credentials
AIRTABLE_API_KEY = "patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3"
AIRTABLE_BASE_ID = "app5s8zl7DsUaDmtx"

# ✅ Table Names
WHATSAPP_TABLE = "whatsapp_table"
OUTREACH_TABLE = "cur_guideline"
DASHBOARD_INBOX_TABLE = "dashboard_inbox"

# ✅ API URLs
WHATSAPP_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{WHATSAPP_TABLE}"
OUTREACH_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{OUTREACH_TABLE}"
DASHBOARD_INBOX_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{DASHBOARD_INBOX_TABLE}"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def record_exists(phone, message):
    """Check if a record with the same phone and message already exists in dashboard_inbox."""
    if not phone or not message:
        return False  # Ignore empty values

    # ✅ Normalize phone number (remove "+", trim spaces)
    normalized_phone = phone.strip().lstrip("+")  

    # ✅ Log the exact values being checked
    logging.info(f"🔍 Checking duplicates for Phone={normalized_phone}, Message={message}")

    # ✅ Properly format filterByFormula (must use double quotes)
    filter_formula = f"AND(phone_number=\"{normalized_phone}\", reply_message_1=\"{message}\")"
    query_url = f"{DASHBOARD_INBOX_URL}?filterByFormula={filter_formula}"

    # ✅ Log query URL for debugging
    logging.info(f"🛠️ Airtable Query: {query_url}")

    response = requests.get(query_url, headers=HEADERS)

    if response.status_code == 200:
        records = response.json().get("records", [])
        
        # ✅ Log the response to check if existing records are found
        logging.info(f"✅ Found {len(records)} valid existing records for deduplication.")

        return len(records) > 0  # True if a matching record is found
    else:
        logging.error(f"❌ Failed to check for duplicates: {response.text}")
        return False  # Assume no duplicate found if API fails

def process_whatsapp_data():
    """Fetch WhatsApp messages, match phone_number to email and photo_url, split last_message, and save to dashboard_inbox."""
    try:
        # ✅ Fetch outreach data (phone-to-email and photo mapping)
        outreach_response = requests.get(OUTREACH_URL, headers=HEADERS)
        outreach_response.raise_for_status()
        outreach_records = outreach_response.json().get("records", [])

        phone_data_map = {
            record["fields"].get("phone", "").strip(): {
                "email": record["fields"].get("email", "").strip(),
                "photo_url": record["fields"].get("photo_url", "").strip()  # ✅ Extract photo_url
            }
            for record in outreach_records if "phone" in record["fields"]
        }
        logging.info(f"Fetched {len(outreach_records)} outreach records.")

        # ✅ Fetch WhatsApp messages
        whatsapp_response = requests.get(WHATSAPP_URL, headers=HEADERS)
        whatsapp_response.raise_for_status()
        whatsapp_records = whatsapp_response.json().get("records", [])

        if not whatsapp_records:
            logging.warning("No WhatsApp messages found.")
            return jsonify({"error": "No WhatsApp messages found"}), 404
        
        logging.info(f"Fetched {len(whatsapp_records)} WhatsApp records.")

        # ✅ Process each WhatsApp record
        saved_count = 0
        for record in whatsapp_records:
            record_id = record["id"]
            fields = record.get("fields", {})

            phone_number = fields.get("phone_number", "").strip()
            last_message = fields.get("last_message", "").strip()
            name = fields.get("Name", "N/A").strip()  # ✅ Extract Name

            logging.info(f"Processing record {record_id}: {fields.keys()}")

            # ✅ Split last_message using regex
            matches = re.findall(r"------------------------\s*(.*?)\s*------------------------\s*(.*)", last_message, re.DOTALL)
            reply_message_1 = matches[0][0].strip() if matches else "N/A"
            reply_message_2 = matches[0][1].strip() if matches else "N/A"

            # ✅ Get email and photo_url from outreach table
            contact_info = phone_data_map.get(phone_number, {})
            email = contact_info.get("email", "N/A")
            profile_picture_url = contact_info.get("photo_url", "")  # May be empty

            # ✅ Check for duplicates before saving
            if record_exists(phone_number, reply_message_1):
                logging.info(f"❌ Duplicate found, skipping: Phone={phone_number}, Message={reply_message_1}")
                continue  # Skip duplicate entries

            # ✅ Prepare data for Airtable update
            save_data = {
                "fields": {
                    "email": email,
                    "name": name,  
                    "phone_number": phone_number if phone_number else "N/A",
                    "reply_message_1": reply_message_1,
                    "reply_message_2": reply_message_2,
                    "profile_picture_url": profile_picture_url  
                }
            }

            # ✅ Send data to dashboard_inbox
            save_response = requests.post(DASHBOARD_INBOX_URL, json=save_data, headers=HEADERS)
            if save_response.status_code == 200:
                saved_count += 1
                logging.info(f"✅ Successfully saved: {save_data}")
            else:
                logging.error(f"❌ Failed to save: {save_response.text}")

        return jsonify({"message": f"Processed and saved {saved_count} records successfully"}), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Airtable API error: {e}")
        return jsonify({"error": str(e)}), 500


