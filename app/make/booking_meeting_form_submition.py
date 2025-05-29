from db.db_ops import db_manager
from flask import request, jsonify

def booking_meeting_form_tracker():
    try:
        # Get JSON payload from the incoming request
        data = request.get_json()
        print("🔹 Incoming Data:", data)

        if not data:
            return jsonify({"error": "No data received"}), 400

        # Extract contact and custom field details
        contact_info = data.get("data", {}).get("contact", {})
        fields = contact_info.get("fields", {})

        email = contact_info.get("email")
        name = fields.get("name")
        phone = fields.get("phone_number")

        # Validate required fields
        if not email or not name or not phone:
            return jsonify({"error": "Email, Name, and Phone are required"}), 400

        # ✅ Include 'email' (the primary key column) in the record
        inbox_record = {
            "email": email,
            "client_id": "taippa_marketing",
            "full_name": name,
            "phone_number": phone
        }

        print(f"🔄 Updating record for: {email}")
        db_manager.update_multiple_fields(
            table_name="booking_records",
            record=inbox_record,
            primary_key_col="email"
        )

        return jsonify({"status": "success", "message": "Booking data updated"}), 200

    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return jsonify({"error": str(e)}), 500
