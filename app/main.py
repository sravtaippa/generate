############################################# Code to Perform Smart Data Mining ############################################# 

# Package imports
import os
from flask import Flask, render_template, request, jsonify
import json
from pyairtable import Table,Api
import requests
import ast
import openai
from urllib.parse import unquote

from pipelines.data_sanitization import fetch_and_update_data, update_email_opens
from pipelines.data_extractor import people_enrichment,people_search,test_run_pipeline,run_demo_pipeline
from pipelines.icp_generation import generate_icp
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf
from pipelines.data_sync import trigger_pipeline
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

print(f"\n=============== Generate : Pipeline started  ===============")
print(f" Directory path for main file: {os.path.dirname(os.path.abspath(__file__))}")
print('Starting the app')
app = Flask(__name__)

@app.route("/testing_connection", methods=["GET"])
def testing_connection():
    try:
        print('------------Started Testing --------------')
        job_titles = request.args.get('job_titles', default='', type=str)
        print((job_titles))
        return {'Status':'Success'}
    except:
        execute_error_block(f"Error occured while testing. {e}")

def construct_query_param(key, values):
    return "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])

def construct_query_param_range(key, values):
    print("&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values]))
    return "&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values])

def construct_query_param_keywords(key, value):
    return f"{key}={value.replace(',', '%2C').replace(' ','%20')}" 

@app.route("/data_sanitization", methods=["GET"])
def initialize_data_sanitization():
    try:
        response = fetch_and_update_data()
        return response
    except Exception as e:
        execute_error_block(f"Error occured while initializing data sanitization module {e}")

@app.route("/generate_lead_magnet", methods=["GET"])
def generate_lead_magnet():
    try:
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
        client_id = "berkleys_homes"
        website_url = "https://berkleyshomes.com/"
        # client_id = "taippa_marketing"
        # website_url = "https://taippa.com/"
        status = generate_icp(client_id,website_url)
        print("Client onboarding successful")
        return {"Status":"Client onboarding successful" if status else "Client onboarding failed"} 
        
    except Exception as e:
        return {"Status":f"Client onboarding failed: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route("/demo_test", methods=["GET"])
def demo_test():
    try:
        # linkedin_url = request.args.get('linkedin_url', type=str)
        # client_id = request.args.get('client_id', type=str)
        linkedin_url = "https://www.linkedin.com/in/isravanbr/"
        client_id = 'berkleys_homes'
        outreach_table = 'outreach_demo'
        status = run_demo_pipeline(linkedin_url,client_id,outreach_table)
        return {"Status":"Demo execution successful" if status else "Failed running demo pipeline"} 

    except Exception as e:
        return {"Status":f"Oops something wrong happened!: {e}"}
        # execute_error_block(f"Error occured while client onboarding : {e}")

@app.route("/scheduled_data_sync", methods=["GET"])
def scheduled_data_sync():
    try:
        status = trigger_pipeline()
        return {"Status":"Successful"}
        # response=fetch_and_update_data(client_id)
        # return {"Status":"Testing sanitization successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

@app.route("/data_ingestion", methods=["GET"])
def execute_collection():
  try:
    print(f"\n------------ Started Data Collection ------------")  

    # Construct the query string dynamically
    client_id = request.args.get('client_id', type=str)
    test_run_id = request.args.get('test_run_id', default='', type=str)
    if not test_run_id:
        # job roles : ceo,coo,cmo,marketing manager,marketing director,investor,partner
        # job seniorities : owner,founder,director,vp,c level,president,vice president
        # keywords : invest
        custom_search_url = request.args.get('custom_search_url', default='', type=str)
        custom_search_url = unquote(custom_search_url)
        print(f"Decoded Custom Search Url added: {custom_search_url}")
        # return {"Status" : custom_search_url}
        qualify_leads = request.args.get('qualify_leads', default='yes', type=str)
        job_titles = request.args.get('job_titles', default='', type=str)
        person_seniorities = request.args.get('person_seniorities', default='', type=str)
        person_locations = request.args.get('person_locations', default='', type=str)
        organization_locations = request.args.get('organization_locations', default='', type=str)
        email_status = request.args.get('email_status', default='', type=str)
        organization_num_employees_ranges = request.args.get('organization_num_employees_ranges', default='', type=str)
        q_keywords = request.args.get('q_keywords',default='',type=str)
        page_number = int(request.args.get('page', default='1', type=str))
        results_per_page = int(request.args.get('per_page', default='1', type=str))
        x =  {"job_titles": job_titles, "person_seniorities": person_seniorities, "person_locations": person_locations, "organization_locations": organization_locations, "email_status": email_status, "organization_num_employees_ranges": organization_num_employees_ranges, "page_number": page_number, "Per page": results_per_page}
        print(f"Collected data : {x}")
        job_titles = job_titles.split(',')
        person_seniorities = person_seniorities.split(',')
        person_locations = ast.literal_eval(person_locations)
        organization_locations = ast.literal_eval(organization_locations)
        if q_keywords!= '' and len(q_keywords)>=0:
            q_keywords = ast.literal_eval(q_keywords)
            if q_keywords == []:
                q_keywords = ''
            else:
                q_keywords = ' '.join(q_keywords)
        email_status = email_status.split(',')
        organization_num_employees_ranges = ast.literal_eval(organization_num_employees_ranges)
        print(f"Here : {organization_num_employees_ranges}")
        print('\n\n') 
        x =  {"job_titles": job_titles, "person_seniorities": person_seniorities, "person_locations": person_locations, "organization_locations": organization_locations, "email_status": email_status, "organization_num_employees_ranges": organization_num_employees_ranges, "page_number": page_number, "Per page": results_per_page}
        print(f"Sanitized data : {x}")
        print('\n\n') 
        query_params = [
            construct_query_param("person_titles", job_titles),
            construct_query_param("person_seniorities", person_seniorities),
            construct_query_param("person_locations", person_locations),
            construct_query_param("organization_locations", organization_locations),
            construct_query_param("contact_email_status", email_status),
            construct_query_param_range("organization_num_employees_ranges", organization_num_employees_ranges),
            construct_query_param_keywords("q_keywords", q_keywords)
        ]
        query_params.append(f"page={page_number}")
        query_params.append(f"per_page={results_per_page}")
        success_status = people_search(custom_search_url,query_params,client_id,qualify_leads)
        response=fetch_and_update_data(client_id)
        print(response)
        print('\n------------ Data Cleaning Completed: Data Ready for Outreach ------------\n')
    else:
        success_status = test_run_pipeline(test_run_id,client_id)
        response=fetch_and_update_data(client_id)
        print(response)
        print('\n------------ Data Cleaning Completed: Data Ready for Outreach ------------\n')
    return {'Status':f'Successfully enriched {success_status} profiles'} if success_status else {'Status':'No profiles enriched.'}
  except Exception as e:
    execute_error_block(f"Error occured while parsing the input. {e}")

if __name__ == '__main__':
  app.run(debug=True)
 