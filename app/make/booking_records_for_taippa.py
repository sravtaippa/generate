import os
import openai
from openai import OpenAI
import json
from db.db_ops import db_manager 


# Create OpenAI client with API key (replace or use environment variable)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "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"))
def extract_appointment_details(email_text):
    system_prompt = (
        "You are an AI that extracts structured event information from raw email text. "
        "Respond ONLY in valid JSON format with the following fields:\n"
        '{\n'
        '  "Event_type": "",\n'
        '  "Invitee": "",\n'
        '  "Invitee_email": "",\n'
        '  "Event_date": "",\n'
        '  "Event_time": "",\n'
        '  "Timezone": "",\n'
        '  "Location": ""\n'
        '}\n'
        "Do not include any explanation or extra text. Output only valid JSON."
    )

    user_prompt = f"Email content:\n{email_text}\n\nExtract the information as specified."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    json_string = response.choices[0].message.content.strip()
    return json.loads(json_string)  # Convert to Python dict

def booking_meeting_tracker(data):
    try:
        # data = {
            # "Text Content": """
            #     Hi Urmi C,

            #     A new Schedule an Appointment with SHIBLA THADATHIL PARAMBIL has been scheduled for 2025-02-28 at 15:30 Europe/Paris

            #     Event Details

            #     Email: shiblashilusaif@gmail.com
            #     Phone: N/A
            #     Country: N/A
            #     Location: https://meet.google.com/yap-tuuv-mba
            #     Password: N/A
            #     Event description:
            #     """

        # }
        result = extract_appointment_details(data["Text_Content"])
        print("Result:", result)
        inbox_record = {
            
            "email": result.get("Invitee_email"),
            "client_id": 'taippa_marketing',
            "full_name": result.get("name"),
            "booking_date_time": result.get("Event_date"),
            "event_type": result.get("Event_type"),
            
                 
        }
        db_manager.insert_data("booking_records", inbox_record) 
        
        
    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise 