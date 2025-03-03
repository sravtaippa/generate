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
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info,add_client_tables_info,add_apollo_webhook_info,fetch_latest_created_time,fetch_record_count_after_time
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf
from pipelines.data_sync import trigger_pipeline
from pipelines.lead_website_analysis import chroma_db_testing,web_analysis
from pipelines.login_email_confirmation import login_email_sender
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

print(f"\n=============== Generate : Pipeline started  ===============")
print(f" Directory path for main file: {os.path.dirname(os.path.abspath(__file__))}")
print('Starting the app')
app = Flask(__name__)

@app.route("/testing_connection", methods=["GET"])
def testing_connection():
    try:
        print('------------Started Testing --------------')
        icp_url = generate_apollo_url(client_id = "cl_berkleys_homes",page_number=1,records_required=2,organization="creativemediahouse.ae")
        return {'icp_url':icp_url}
    except Exception as e:
        execute_error_block(f"Error occured while testing. {e}")

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
        response = fetch_and_update_data()
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

@app.route("/scheduled_data_sync", methods=["GET"])
def scheduled_data_sync():
    try:
        start_time = time.time()  # Start timer
        status = trigger_pipeline()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

if __name__ == '__main__':
  app.run(debug=True,use_reloader=False)
 