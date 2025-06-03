############################################# Code to Perform Smart Data Mining ############################################# 

# Package imports
import os
from flask import Flask, render_template, request, jsonify
from urllib.parse import unquote
import time

from pipelines.data_sanitization import fetch_and_update_data, update_email_opens, test_sanitize
from pipelines.data_sanitization import update_email_opens
from pipelines.data_extractor import people_enrichment,test_run_pipeline,run_demo_pipeline
from pipelines.guideline_data_sync import parse_contacts,influencer_marketing
from db.table_creation import create_client_tables
from pipelines.icp_generation import generate_icp,generate_apollo_url
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info,add_client_tables_info,add_apollo_webhook_info,fetch_latest_created_time,fetch_record_count_after_time,phone_number_updation
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf,test_run
from pipelines.data_sync import trigger_pipeline_custom,trigger_custom_pipeline
from pipelines.lead_website_analysis import chroma_db_testing,web_analysis
from pipelines.login_email_confirmation import login_email_sender
from outreach.add_leads import add_lead_leadsin
from outreach.campaign_metrics import update_linkedin_campaign_metrics
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from dashboard.dashboard_updation import process_whatsapp_data
from dashboard.client_onboarding_update_form import update_client_onboarding
from dashboard.client_configuration_form import update_client_configuration
from dashboard.client_profile_picture import get_profile_picture
from dashboard.email_dashboard import fetch_recent_leads_from_db, fetch_metric_value, get_booking_count, email_sent_chart, get_campaign_details, fetch_leads, get_user_campaigns, get_campaign_metrics, get_lead_details
from dashboard.leads_email import generate_csv_and_send_email
from dashboard.test_databse import run_database_test
from dashboard.linkedin_dashboard import get_linkedin_metrics, get_linkedin_campaign_details, get_linkedin_statistics, get_linkedin_replies, get_linkedin_leads_by_username
from pipelines.organization_list_enrichment import fetch_organization_domains
# from pipelines.guideline_generate import generate_content_guideline
from pipelines.data_sanitization_psql import sanitize_data
from pipelines.guideline_generate import execute_generate_sequence
from pipelines.guideline_outreach import execute_outreach_sequence

from make.linkedIn_message_sent_tracker import linkedin_message_sent_tracker
from make.linkedIn_invite_sent_tracker import linkedin_invite_sent_tracker
from make.linkedIn_invite_accepted_tracker import linkedin_invite_accepted_tracker
from make.email_sent import email_sent_tracker
from make.ai_response_module import linkedin_ai_response_tracker
from email_module.generic_email_module import send_html_email
from make.email_post_response import email_post_response_tracker
from  make.booking_records_for_taippa import booking_meeting_tracker
from make.booking_meeting_form_submition import booking_meeting_form_tracker
print(f"\n =============== Generate : Pipeline started  ===============")

print(f" Directory path for main file: {os.path.dirname(os.path.abspath(__file__))}")
print('Starting the app')
app = Flask(__name__)

@app.route("/guideline_outreach", methods=["GET"])
def guideline_outreach():
    try:
        start_time = time.time()  # Start timer
        outreach_status = execute_outreach_sequence()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return outreach_status
    except Exception as e:
        print(f"Error occured while generating the content for outreach: {e}")

@app.route("/guideline_generate", methods=["GET"])
def guideline_generate():
    try:
        start_time = time.time()  # Start timer
        generate_status = execute_generate_sequence()
        end_time = time.time()  # End timer
        elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
        print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return generate_status
    except Exception as e:
        print(f"Error occured while generating the content for outreach: {e}")

# @app.route("/guideline_generate", methods=["GET"])
# def guideline_generate():
#     try:
#         generate_content_guideline()
#         return {"Status":"Successfully fetched organization list"}
#     except Exception as e:
#         print(f"Error occured while generating the content for outreach: {e}")

@app.route("/organization_list_enrichment", methods=["GET"])
def organization_list_enrichment():
    try:
        # print(f"Fetching organization list")
        # fetch_organization_domains(1)
        # print(f"Successfully fetched organization list")
        return {"Status":"Successfully fetched organization list"}
    except Exception as e:
        print(f"Error occured while fetching organization list: {e}")

@app.route("/guideline_data_sync", methods=["GET"])
def sync_data_guideline():
    try:
        print(f"Syncing data for guideline")
        influencer_marketing()
        # parse_contacts()
        return {"Status":"Data sync successful"}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

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
        status = add_lead_leadsin(apollo_id,campaign_id,outreach_table_name)
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
# # test datasanitization
# @app.route("/test_sanitize_new", methods=["GET"])
# def test_sanitize_new():
#     try:
#         response = test_sanitize()
#         return response
#     except Exception as e:
#         execute_error_block(f"Error occured while counting email opened and email clicked {e}")
#         @app.route("/test_sanitize_new", methods=["GET"])



@app.route("/test_sanitize_psql", methods=["POST"])
def test_sanitize_psql():
    try:
        data = request.get_json(force=True)

        client_id = data.get("client_id")
        data_dict = data.get("data")  # <-- FIXED HERE

        if not client_id or not data_dict:
            return jsonify({"error": "Missing client_id or data"}), 400

        response = sanitize_data(client_id, data_dict)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500




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

# @app.route("/scheduled_data_sync_generic", methods=["GET"])
# def scheduled_data_sync_generic():
#     try:
#         start_time = time.time()  
#         status = trigger_pipeline_generic()
#         end_time = time.time()  
#         elapsed_minutes = (end_time - start_time) / 60
#         print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
#         return {"Status":"Successful"}
#     except Exception as e:
#         print(f"Exception occured during scheduled data sync: {e}")
#         execute_error_block(f"Exception occured during scheduled data sync: {e}")

# @app.route("/scheduled_data_sync", methods=["GET"])
# def scheduled_data_sync():
#     try:
#         start_time = time.time()  # Start timer
#         status = trigger_pipeline_custom()
#         end_time = time.time()  # End timer
#         elapsed_minutes = (end_time - start_time) / 60  # Convert seconds to minutes
#         print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
#         return {"Status":"Successful"}
#     except Exception as e:
#         print(f"Exception occured during scheduled data sync: {e}")
#         execute_error_block(f"Exception occured during scheduled data sync: {e}")

# 127.0.0.1:8080/scheduled_data_sync_custom?client_id=guideline
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

@app.route("/run_pipeline_check", methods=["GET"])
def run_pipeline_check():
    try:
        print(f"Testing pipeline run")
        status = "True"
        # print(f"~~~~~~~~~ Execution Time: {elapsed_minutes:.2f} minutes ~~~~~~~~~~~~")
        return {"Status":"Test pipeline execution successful"}
    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}

@app.route("/lead_magnet_generate")
def lead_magnet_generate():
    try:
        # linkedin_url = "http://www.linkedin.com/in/galeapatricia"
        # linkedin_url = "http://www.linkedin.com/in/akshay-patil-digital"
        linkedin_url = request.args.get('linkedin_url', type=str)
        user_id = "sravan.workemail@gmail.com"
        print(f"Testing lead magnet")
        generate_lead_magnet_pdf(user_id,linkedin_url)
        return test_run()
    except Exception as e:
        print(f"Error occured while testing lead magnet: {e}")

#Email dashboard 
@app.route("/get_profile_picture_dashboard/<username>", methods=["GET"])
def get_profile_picture_dashboard(username):
    # username = request.args.get('username', type=str)
    return   get_profile_picture(username)

@app.route("/get_recent_leads_dashboard/<username>", methods=["GET"])
def get_recent_leads_dashboard(username):
    data, status = fetch_recent_leads_from_db(username)
    return jsonify(data), status

@app.route("/get_statistics_dashboard", methods=["GET"])
def get_statistics_dashboard():
    username = request.args.get("username")
    field = request.args.get("field")

    if not username or not field:
        return jsonify({"error": "Missing 'username' or 'field' parameter"}), 400

    value = fetch_metric_value(username, field)
    return jsonify({"value": value}), 200

@app.route("/get_booking_count_dashboard", methods=["GET"])
def get_booking_count_dashboard():
    username = request.args.get("username", default=None)
    
    if not username:
        # If 'username' is missing, use 0 as the value
        value = 0
    else:
        value = get_booking_count(username)
    
    return jsonify({"value": value}), 200

@app.route("/get_email_sent_chart_dashboard/<username>", methods=["GET"])
def get_email_sent_chart_dashboard(username):
    return email_sent_chart(username)

@app.route("/get_campaign_details_dashboard/<username>", methods=["GET"])
def get_campaign_details_dashboard(username):
    return get_campaign_details(username)


@app.route("/get_recent_replies_dashboard", methods=["GET"])
def get_recent_replies_dashboard():
    user_id = request.args.get("username")  # assuming username = client_id
    if not user_id:
        return {"error": "Username is required"}, 400

    try:
        data = fetch_leads(user_id)  # Pass user_id to fetch_leads
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    

@app.route("/get_user_campaigns_dashboard", methods=["GET"])
def get_user_campaigns_dashboard():
    user_id = request.args.get("username")  # assuming username = client_id
    if not user_id:
        return {"error": "Username is required"}, 400

    try:
        data = get_user_campaigns(user_id)  # <-- Pass user_id explicitly
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500

    
@app.route("/get_campaign_metrics_dashboard", methods=["POST"])
def get_campaign_metrics_dashboard():
    data = request.get_json()
    campaign_id = data.get("campaign_id")

    if not campaign_id:
        return {"error": "Campaign id is required"}, 400

    try:
        metrics = get_campaign_metrics(campaign_id)
        return {"data": metrics}, 200
    except Exception as e:
        return {"error": f"Error fetching campaign metrics: {str(e)}"}, 500

@app.route("/get_lead_details_dashboard", methods=["GET"])
def get_lead_details_dashboard():
    user_id = request.args.get("username")
    email = request.args.get("email")

    if not user_id or not email:
        return {"error": "Username or Email is required"}, 400

    try:
        data = get_lead_details(user_id, email)
        return {"data": data}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/linkedin_metrics_table_dashboard", methods=["GET"])
def linkedin_metrics_table_dashboard():
    client_id = request.args.get("client_id")   # ← keep the name consistent
    if not client_id:
        return jsonify({"error": "client_id is required"}), 400

    try:
        data = get_linkedin_metrics(client_id)
        return jsonify({"data": data}), 200
    except ValueError as ve:
        # custom “not found” error from helper
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        # anything else = 500
        return jsonify({"error": str(e)}), 500
    
# @app.route("/linkedin_campaign_details_dashboard", methods=["GET"])
# def linkedin_campaign_details_dashboard():
#     username = request.args.get("username")
#     if not username:
#         return jsonify({"error": "username is required"}), 400

#     try:
#         data = get_linkedin_campaign_details(username)
#         return jsonify({"data": data}), 200
#     except ValueError as ve:
#         return jsonify({"error": str(ve)}), 404
#     except Exception as e:
#         return jsonify({"error": "Internal server error"}), 500
@app.route("/linkedin_campaign_details_dashboard/<username>", methods=["GET"])
def linkedin_campaign_details_dashboard(username):
    return get_linkedin_campaign_details(username)

@app.route("/get_linkedin_statistics_dashboard", methods=["GET"])
def get_linkedin_statistics_dashboard():
    username = request.args.get("username")
    field = request.args.get("field")

    if not username or not field:
        return jsonify({"error": "Missing 'username' or 'field' parameter"}), 400

    data = get_linkedin_statistics(username, field)

    if data is None:
        return jsonify({"error": "No campaign found for user"}), 404

    return jsonify(data), 200

@app.route("/get_linkedin_replies_dashboard", methods=["GET"])
def get_linkedin_replies_dashboard():
    username = request.args.get("username")
    
    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    data = get_linkedin_replies(username)

    if data is None:
        return jsonify({"error": "Failed to fetch leads"}), 500

    return jsonify({"leads": data}), 200

@app.route("/get_linkedin_leads_dashboard", methods=["GET"])
def get_linkedin_leads_dashboard():
    username = request.args.get("username")
    
    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    data, status = get_linkedin_leads_by_username(username)
    return jsonify(data), status

    return jsonify({"leads": data}), 200
@app.route("/fetch_airtable_data_and_create_csv", methods=["GET"])
def trigger_csv_generation():
    return generate_csv_and_send_email()



@app.route("/test_db",methods=["GET"])
def connect_db():
    try:
        test()
        return {"Status":"Testing completed"}
    except Exception as e:
        print(f"Error occured while testing connection")

#Make Scenarios
@app.route("/run_linkedin_message_sent_tracker", methods=["GET"])
def run_linkedin_message_sent_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_message_sent_tracker(data)
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/run_linkedin_invite_sent_tracker", methods=["GET"])
def run_linkedin_invite_sent_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_invite_sent_tracker(data)
        # linkedin_invite_sent_tacker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500  
     
@app.route("/run_linkedin_invite_accepted_tracker", methods=["GET"])
def run_linkedin_invite_accepted_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture
        }
        linkedin_invite_accepted_tracker(data)
        # linkedin_invite_accepted_tacker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500   

@app.route("/run_linkedin_ai_response_tracker", methods=["GET"])
def run_linkedin_ai_response_tracker():
    try:
        thread_id = request.args.get("thread_id", default=None)
        campaign_name = request.args.get("campaign_name", default=None)
        linkedin_profile_url = request.args.get("linkedin_profile_url", default=None)
        full_name = request.args.get("full_name", default=None)
        email = request.args.get("email", default=None)
        picture = request.args.get("picture", default=None)
        response_message = request.args.get("response_message", default=None)
        sentiment = request.args.get("response_message", sentiment=None)

        data = {
            "thread_id": thread_id,
            "campaign_name": campaign_name,
            "linkedin_profile_url": linkedin_profile_url,
            "full_name": full_name,
            "email": email,
            "picture": picture,
            "response_message": response_message,
            "sentiment": sentiment
        }

        linkedin_ai_response_tracker(data)
        return {"status": "success", "message": "Testing completed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/send_generic_email", methods=["GET"])
def send_generic_email():
    try:
        html_content = """
            <p>Hi Mag,</p>
            <p>We've received a response for the <strong>"Guideline Middle East"</strong> campaign via LinkedIn.</p>
            <h4>Lead Details:</h4>
            <ul>
            <li><strong>Name:</strong> John Doe</li>
            <li><strong>LinkedIn:</strong> https://linkedin.com/in/johndoe</li>
            <li><strong>Message:</strong> "Looking forward to speaking."</li>
            </ul>
            <br>
            This is an automated message generated by our lead capture system.
            <br>
            <p>Best,<br>Team Generate</p>
            """

        send_html_email(
            to_email='shiblashilu@gmail.com',
            subject='New Lead Response - Guideline Middle East',
            html_content=html_content,
            cc_emails=['sravan@taippa.com', 'shilusaifshilu@gmail.com.com']
        )
        return {"status": "success", "message": "email Sent Successfully"}

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_email_sent_tracker", methods=["GET"])
def run_email_sent_tracker():
    try:
       
        email_sent_tracker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_email_post_response_tracker", methods=["GET"])
def run_email_post_response_tracker():
    try:
       
        email_post_response_tracker()
        return {"status": "success", "message": "Testing completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/run_booking_meeting_tracker", methods=["GET"])
def run_booking_meeting_tracker():
    try:
        # Text_Content = request.args.get("Text_Content", default=None),
        email= request.args.get("Invitee_email", default=None),        
        full_name= request.args.get("Invitee", default=None),
        booking_date_time= request.args.get("Event_date", default=None),
        event_type= request.args.get("event_type", default=None),
        
        data = {
            "email": email,            
            "full_name": full_name,
            "booking_date_time": booking_date_time,
            "event_type":event_type
        }

        booking_meeting_tracker(data)
        return {"status": "success", "message": "Booking tracker completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    
@app.route("/run_booking_meeting_form_tracker", methods=["POST"])
def run_booking_meeting_form_tracker():
    try:
        return booking_meeting_form_tracker()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == '__main__':
#   app.run(debug=True,use_reloader=False)
#   app.run(port=8001) 
  app.run(host="127.0.0.1", port=5000)
