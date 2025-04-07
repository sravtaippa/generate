############################################# Code to Perform Smart Data Mining ############################################# 

# Package imports
import os
from flask import Flask, render_template, request, jsonify
from urllib.parse import unquote
import time

from pipelines.data_sanitization import fetch_and_update_data, update_email_opens
from pipelines.data_extractor import people_enrichment,test_run_pipeline,run_demo_pipeline
from db.table_creation import create_client_tables
from pipelines.icp_generation import generate_icp,generate_apollo_url
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info,add_client_tables_info,add_apollo_webhook_info,fetch_latest_created_time,fetch_record_count_after_time,phone_number_updation
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf
from pipelines.data_sync import trigger_pipeline_custom,trigger_custom_pipeline
from pipelines.lead_website_analysis import chroma_db_testing,web_analysis
from pipelines.login_email_confirmation import login_email_sender
from outreach.add_leads import add_lead_to_campaign
from outreach.campaign_metrics import update_linkedin_campaign_metrics
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from dashboard.dashboard_updation import process_whatsapp_data
from dashboard.client_onboarding_update_form import update_client_onboarding
from dashboard.client_configuration_form import update_client_configuration
print(f"\n =============== Generate : Pipeline started  ===============")

print(f" Directory path for main file: {os.path.dirname(os.path.abspath(__file__))}")
print('Starting the app')
app = Flask(__name__)

@app.route("/update_client_configuration_form", methods=["GET"])
def update_client_configuration_form():
    return  update_client_configuration()

@app.route("/update_client_onboarding_form", methods=["GET"])
def update_client_onboarding_form():
    return  update_client_onboarding()

@app.route("/add_leads_linkedin", methods=["GET"])
def add_leads_linkedin():
    try:
        # test url : 127.0.0.1:5000/linkedin_outreach?apollo_id=54a75889746869730aeb332c&campaign_id=316135&outreach_table_name=outreach_guideline
        linkedin_profile_url = request.args.get('linkedin_profile_url', type=str)
        apollo_id = request.args.get('apollo_id', type=str)
        cur_table_name = request.args.get('cur_table_name', type=str)
        photo_url = request.args.get('photo_url', type=str)
        campaign_id = request.args.get('campaign_id', type=str)
        recipient_full_name = request.args.get('recipient_full_name', type=str)
        recipient_email = request.args.get('recipient_email', type=str)
        recipient_company = request.args.get('recipient_company', type=str)
        linkedin_message = request.args.get('linkedin_message', type=str)
        linkedin_message2 = request.args.get('linkedin_message2', type=str)
        linkedin_subject = request.args.get('linkedin_subject', type=str)
        linkedin_connection_message = request.args.get('linkedin_connection_message', type=str)
        linkedin_leads_table_name = "linkedin_leads"
        data = {
            "thread_id":"NA",
            "apollo_id":apollo_id,
            "campaign_id":campaign_id,
            "full_name":recipient_full_name,
            "email":recipient_email,
            "linkedin_profile_url":linkedin_profile_url,
            "company":recipient_company,
            "message":linkedin_message,
            "message_2":linkedin_message2,
            "linkedin_subject":linkedin_subject,
            "linkedin_connection_message":linkedin_connection_message
        }
        export_to_airtable(data,linkedin_leads_table_name)
        return {"Status":"Successfully added the lead to the leads table"} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

@app.route("/segregate_whatsapp_info", methods=["GET"])
def segregate_whatsapp_info():
    return process_whatsapp_data()

@app.route('/update_campaign_metrics',methods=['GET'])
def update_campaign_metrics():
    try:
        # test url 127.0.0.1:5000/update_campaign_metrics?campaign_id=316135
        campaign_id = request.args.get('campaign_id', type=str)
        status = update_linkedin_campaign_metrics(campaign_id)
        return {"Campaign Update Status":str(status)}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route('/linkedin_outreach',methods=['GET'])
def linkedin_outreach():
    try:
        # test url : 127.0.0.1:5000/linkedin_outreach?apollo_id=54a75889746869730aeb332c&campaign_id=316135&outreach_table_name=outreach_guideline
        apollo_id = request.args.get('apollo_id', type=str)
        campaign_id = request.args.get('campaign_id', type=str)
        outreach_table_name = request.args.get('outreach_table_name', type=str)
        print(f"apollo_id: {apollo_id}, campaign_id: {campaign_id}, outreach_table_name: {outreach_table_name}")
        status = add_lead_to_campaign(apollo_id,campaign_id,outreach_table_name)
        return {"Status":str(status)} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route('/fetch_records', methods=['GET'])
def fetch_records():
    try:
        # Get `inputed_created_time` from query parameters
        inputed_created_time = request.args.get("inputed_created_time")
        
        if not inputed_created_time:
            return jsonify({"error": "Missing inputed_created_time parameter"}), 400
        
        try:
            # Ensure the input datetime is correctly formatted
            datetime.datetime.strptime(inputed_created_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS.ssssss"}), 400

        # Convert input time to Airtable's required ISO 8601 format
        inputed_created_time_iso = datetime.datetime.strptime(inputed_created_time, "%Y-%m-%d %H:%M:%S.%f").isoformat()

        # Correct filter formula to compare with `created_time` field
        filter_formula = f"{{created_time}} > '{inputed_created_time_iso}'"

        params = {
            "filterByFormula": filter_formula,
            "fields[]": ["apollo_id", "recipient_first_name", "created_time"]
        }

        response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data", "details": response.text}), 500

        data = response.json()
        records = [
            {
                "apollo_id": str(record["fields"].get("apollo_id", "")),  # Ensure long text is handled properly
                "recipient_first_name": str(record["fields"].get("recipient_first_name", "")),  # Convert to string
                "created_time": record["fields"].get("created_time", "")
            }
            for record in data.get("records", [])
        ]

        return jsonify({"records": records})
    except Exception as e:
        execute_error_block(f"Error occurred while fetching latest records from the outreach table for LinkedIn: {e}")

@app.route("/testing_connection", methods=["GET"])
def testing_connection():
    try:
        print('------------Started Testing --------------')
        # icp_url = generate_apollo_url(client_id = "cl_berkleys_homes",page_number=1,records_required=2,organization="creativemediahouse.ae")
        return {'Status':"Hello World"}
    except Exception as e:
        execute_error_block(f"Error occured while testing. {e}")

@app.route('/get_phone_numbers', methods=['GET'])
def retrieve_phone_numbers():
    try:
        apollo_id = request.args.get('apollo_id', type=str)
        cur_table_name = request.args.get('cur_table_name', type=str)
        outreach_table_name = request.args.get('outreach_table_name', type=str)
        print(f"apollo_id: {apollo_id}, cur_table_name: {cur_table_name}, outreach_table_name: {outreach_table_name}")
        phone = phone_number_updation(apollo_id,cur_table_name,outreach_table_name)
        return {"phone":phone}
    except Exception as e:
        execute_error_block(f"Error occured while fetching phone numbers. {e}")

@app.route('/apollo_webhook', methods=['POST'])
def apollo_webhook():
    try:
        def get_sanitized_phone_number(data):
            try:
                return data.get('people', [{}])[0].get('phone_numbers', [{}])[0].get('sanitized_number', 'NA')
            except (IndexError, KeyError, TypeError):
                return "NA"
        
        received_data = request.get_json()
        print("Received data:", received_data)
        apollo_table = "apollo_webhook"
        phone = get_sanitized_phone_number(received_data)
        apollo_id = str(received_data['people'][0]['id'])
        data = {
            "apollo_id":apollo_id,
            "response":str(received_data),
            "phone":str(phone)
        }
        add_apollo_webhook_info(data,apollo_table)
        return jsonify({"status": "success", "message": "Data received"}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/data_sanitization", methods=["GET"])
def initialize_data_sanitization():
    try:
        client_id = request.args.get('client_id', type=str)
        if client_id in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}")
            return {"Status":f"Invalid information passed. client_id : {client_id}"}
        print(f"Fetched parameters-> client_id : {client_id}")
        response = fetch_and_update_data(client_id)
        return response
    except Exception as e:
        execute_error_block(f"Error occured while initializing data sanitization module {e}")

@app.route("/web_analysis", methods=["GET"])
def analyze_website():
    try:
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        apollo_tags = web_analysis(website_url,client_id)
        return {"apollo_tags":apollo_tags}
    except Exception as e:
        execute_error_block(f"Error occured while initializing analyzing website module {e}")

@app.route("/generate_lead_magnet", methods=["GET"])
def generate_lead_magnet():
    try:
        # generate_lead_magnet?linkedin_url=https://www.linkedin.com/in/nithin-paul-7063b1183/&email_id=sravzone@gmail.com
        linkedin_url = request.args.get('linkedin_url', type=str)
        email_id = request.args.get('email_id', type=str)
        print(f"Linkedin url: {linkedin_url}")
        print(f"Email id: {email_id}")
        response = generate_lead_magnet_pdf(email_id,linkedin_url)
        print(response)
        return response
    except Exception as e:
        execute_error_block(f"Error occured while generating lead magnet {e}")

@app.route("/update-email-opens", methods=["GET"])
def update_email_opens_clicked():
    try:
        response = update_email_opens()
        return response
    except Exception as e:
        execute_error_block(f"Error occured while counting email opened and email clicked {e}")

@app.route("/test_chroma",methods=["GET"])
def test_chroma():
    try:
        status = chroma_db_testing()
        return {"Status":status}
    except Exception as e:
        print(f"Error occured while testing chroma db sqlite version")

@app.route("/test_sanitization", methods=["GET"])
def test_sanitization():
    try:
        client_id="plot_taippa"
        response=fetch_and_update_data(client_id)
        return {"Status":"Testing sanitization successful"}
    except Exception as e:
        print(f"Exception occured while testing sanitization module : {e}")

@app.route("/fetch-inbox-details", methods=["GET"])
def fetch_inbox_details_full():
    try:
        response = fetch_inbox_details()
        return response
    except Exception as e:
        execute_error_block(f"Error occured while fetching inbox details : {e}")

@app.route("/client_onboarding", methods=["GET"])
def client_onboarding():
    try:
        # 127.0.0.1:5000/client_onboarding?client_id=upgrade&website_url=https://www.upgrade-now.com/b2b-sales-agency-en-2&recipient_email=sravzone@gmail.com&recipient_name=Srav&password=upgrade123
        start_time = time.time()  # Start timer
        print(f"\n\n------------- Client Onboarding Process Started for client_id-----------------\n\n")
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        password = request.args.get('password', type=str)
        recipient_name = request.args.get('recipient_name', 'Customer')
        recipient_email = request.args.get('recipient_email')
        if client_id in ["",None] or website_url in ["",None] or password in ["",None] or recipient_email in ["",None] or recipient_name in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
            return {"Status":f"Invalid information passed. client_id : {client_id}, website_url: {website_url}"}
        print(f"Fetched parameters-> client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
        src_table, cur_table, outreach_table = create_client_tables(client_id)
        print(f"------ Client tables created for client_id : {client_id} -------------")
        add_client_tables_info(client_id,src_table,cur_table,outreach_table)
        print(f"------ Added client tables info to the airtable for client_id : {client_id} -------------")
        status = generate_icp(client_id,website_url)
        print(f"------ Successfully generated ICP and stored client details in Vector database: {client_id} -------------")
        print(f"\n\n------------Sending Email to Client for credentials --------------------\n\n")
        login_email_sender(recipient_name,recipient_email,client_id,password)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        print("\n\n=======================Client onboarding completed successfuly======================\n\n")
        return {"Status":"Client onboarding process completed" if status else "Client onboarding process failed"}
    except Exception as e:
        return {"Status":f"Client onboarding process failed: {e}"}

@app.route("/client_onboarding_test", methods=["GET"])
def client_onboarding_test():
    try:
        start_time = time.time()  # Start timer
        print(f"\n\n------------- Client Onboarding Process Started for client_id-----------------\n\n")
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        password = request.args.get('password', type=str)
        recipient_name = request.args.get('recipient_name', 'Customer')
        recipient_email = request.args.get('recipient_email')
        if client_id in ["",None] or website_url in ["",None] or password in ["",None] or recipient_email in ["",None] or recipient_name in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
            return {"Status":f"Invalid information passed. client_id : {client_id}, website_url: {website_url}"}
        print(f"Fetched parameters-> client_id : {client_id}, website_url: {website_url}, recipient_email {recipient_email}, password: {password}, recipient_name: {recipient_name}")
        src_table, cur_table, outreach_table = create_client_tables(client_id)
        print(f"------ Client tables created for client_id : {client_id} -------------")
        add_client_tables_info(client_id,src_table,cur_table,outreach_table)
        print(f"------ Added client tables info to the airtable for client_id : {client_id} -------------")
        status = generate_icp(client_id,website_url)
        print(f"------ Successfully generated ICP and stored client details in Vector database: {client_id} -------------")
        print("\n\n--------Started Data Sync ---------\n\n")
        trigger_pipeline()
        print("\n\n--------Completed Data Sync ---------\n\n")
        print("Client onboarding successful")
        print(f"\n\n------------Sending Email to Client for credentials --------------------\n\n")
        login_email_sender(recipient_name,recipient_email,client_id,password)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        print("\n\n=======================Client onboarding completed successfuly======================\n\n")
        return {"Status":"Client onboarding process completed" if status else "Client onboarding process failed"}
    except Exception as e:
        return {"Status":f"Client onboarding process failed: {e}"}
    
@app.route("/demo_test", methods=["GET"])
def demo_test():
    try:
        linkedin_url = request.args.get('linkedin_url', type=str)
        client_id = request.args.get('client_id', type=str)
        # linkedin_url = "https://www.linkedin.com/in/isravanbr/"
        # client_id = 'berkleys_homes'
        outreach_table = 'outreach_demo'
        status = run_demo_pipeline(linkedin_url,client_id,outreach_table)
        return {"Status":"Demo execution successful" if status else "Failed running demo pipeline"} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route("/scheduled_data_sync_generic", methods=["GET"])
def scheduled_data_sync_generic():
    try:
        start_time = time.time()  
        status = trigger_pipeline_generic()
        end_time = time.time()  
        elapsed_minutes = (end_time - start_time) / 60
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

@app.route("/scheduled_data_sync", methods=["GET"])
def scheduled_data_sync():
    try:
        start_time = time.time()  # Start timer
        status = trigger_pipeline_custom()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

@app.route("/scheduled_data_sync_custom", methods=["GET"])
def scheduled_data_sync_custom():
    try:
        # /scheduled_data_sync_custom?client_id=possible_event
        start_time = time.time()  # Start timer
        client_id = request.args.get('client_id', type=str)
        if client_id in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}")
            return {"Status":f"Invalid information passed. client_id : {client_id}"}
        status = trigger_custom_pipeline(client_id)
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

if __name__ == '__main__':
  app.run(debug=True,use_reloader=False)
 