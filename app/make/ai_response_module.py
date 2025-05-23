import os
import openai
from openai import OpenAI
from db.db_ops import db_manager
from config import OPENAI_API_KEY
# Create OpenAI client with API key (replace or use environment variable)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def classify_linkedin_message(message_text):
    system_prompt = """You are an AI agent designed to analyze LinkedIn messages from leads and classify them as either "Positive" or "Negative".

Classification Criteria:

Positive:
- Agreement or enthusiasm
- Requests for more details or next steps
- Expressions of approval

Negative:
- Direct rejections or disagreements
- Requests to be removed from communication
- Neutral responses that do not show interest

Rules:
- If the message shows any level of interest, classify it as "Positive."
- If the message is neutral or negative in tone, classify it as "Negative."
- Do not classify ambiguous messages as "Positive" unless there is a clear intent to engage.

Output:
Return only one of the following labels:
1) Positive
2) Negative
"""

    user_prompt = f'This is the LinkedIn message text received from the lead: "{message_text}"\n\nClassify this message based on the criteria.'

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()

# # Example usage
# if __name__ == "__main__":
#     test_message = "I’m not interested at this time, but thanks for reaching out"
#     result = classify_linkedin_message(test_message)
#     print("Classification:", result)

def linkedin_ai_response_tacker(message):
    try:
        
        sentiment= classify_linkedin_message(message)
        print("Classification:", sentiment)
        data = {
            "thread_id": "influencer_marketing_60d2165a8530680001f38bd8",
            "campaign_name": "influencer_marketing",
            "linkedin_profile_url": "http://www.linkedin.com/in/pj-leimgruber",
            "full_name": "Magda Houalla",
            "email": "magdaoualla@gmail.com",
            "picture": "https://media.licdn.com/dms/image/v2/D5603AQHeEZ4rcWOAXg/profile-displayphoto-shrink_200_200/profile-displayphoto-shrink_200_200/0/1728920716356?e=1750291200&v=beta&t=Xhuu3diZgNeydUQs0OE2zPQOwH5L3321gUHQVYSuwBo"
        }
        table_name = "leadsin_response_linkedin"
        column_name = "campaign_name"
        unique_value = "linkedin_profile_url"
        duplicate=db_manager.unique_key_check(column_name, unique_value, table_name)
        # i need to print duplicated record if it is found
        # i need to fetch thread_id also
        if duplicate is False and sentiment == "Positive":
            cols_list = ['campaign_name', 'linkedin_profile_url']
            col_values = ['influencer_marketing', 'http://www.linkedin.com/in/carlybrower']
            leadsrecords = db_manager.get_records_with_filter("linkedin_leads", cols_list, col_values, limit=1)
            if isinstance(leadsrecords, dict):
                leadsrecords = [leadsrecords]
            print(f"🔢 Matching Record Count in linkedin_leads: {len(leadsrecords)}")

            if len(leadsrecords) == 1:
                print(f"🛠 Only one matching record found in linkedin_leads. Updating status to Positive.")
                if leadsrecords:
                    record = leadsrecords[0]  # Pick the first one if available
                    db_manager.update_single_field(
                        table_name="linkedin_leads",
                        column_name='status',
                        column_value="Positive",
                        primary_key_col='thread_id',
                        primary_key_value=record['thread_id']
                    )
                    print(f"✅ Record updated status to {sentiment} successfully.")

                    db_manager.insert_data(table_name, data)
                    print("Completed linkedin response table updation")  
        if sentiment == "Negative":
            cols_list = ['campaign_name', 'linkedin_profile_url']
            col_values = ['influencer_marketing', 'http://www.linkedin.com/in/carlybrower']
            leadsrecords = db_manager.get_records_with_filter("linkedin_leads", cols_list, col_values, limit=1)
            if isinstance(leadsrecords, dict):
                leadsrecords = [leadsrecords]
            print(f"🔢 Matching Record Count in linkedin_leads: {len(leadsrecords)}")

            if len(leadsrecords) == 1:
                print(f"🛠 Only one matching record found in linkedin_leads. Updating status to Negative.")
                if leadsrecords:
                    record = leadsrecords[0]  # Pick the first one if available
                    db_manager.update_single_field(
                        table_name="linkedin_leads",
                        column_name='status',
                        column_value="Negative",
                        primary_key_col='thread_id',
                        primary_key_value=record['thread_id']
                    )
                    print(f"✅ Record updated status to {sentiment} successfully.")

                    db_manager.insert_data(table_name, data)
                    print("Completed linkedin response table updation")             

    except Exception as e:
        print(f"❌ Error during DB test: {e}")
        raise
