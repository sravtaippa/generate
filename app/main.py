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
from pipelines.data_extractor import people_enrichment,people_search
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

print(f"\n=============== Generate : Data Ingestion  ===============")
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
        user_id = request.args.get('user_id', default='sravan.workemail@gmail.com', type=str)
        print(f"User id: {user_id}")
        response = generate_lead_magnet_pdf(user_id)
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

def test_run_pipeline(test_run_id,client_id):
    try:
        record_exists = unique_key_check_airtable('id',test_run_id)
        if record_exists:
            print(f'Record with the following id: {test_run_id} already exists. Skipping the entry...')
            return True
        enrichment_api_response = people_enrichment(test_run_id)
        if enrichment_api_response.status_code == 200:
            data = enrichment_api_response.json()
            data=data['person']
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "gpt-4" for more advanced results
                messages=[
                    {"role": "system", "content": "You are an expert at text summarization."},
                    {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
                ],
                max_tokens=100  # Adjust based on the desired length of the output
                )
            employment_summary = response['choices'][0]['message']['content']
            data_dict = {
                    'id': data['id'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'name': data['name'],
                    'email': 'sravan.workemail@gmail.com',
                    'linkedin_url': data['linkedin_url'],
                    'associated_client_id': client_id,
                    'title': data['title'],
                    'seniority': data['seniority'],
                    'headline': data['headline'],
                    'is_likely_to_engage': 'True',
                    'photo_url': data['photo_url'],
                    'email_status': "verified",
                    'twitter_url': data['twitter_url'],
                    'github_url': data['github_url'],
                    # 'facebook_url': data['facebook_url'],
                    'employment_history': str(data['employment_history']),
                    'employment_summary':str(employment_summary),
                    'organization_name': data['organization']['name'],
                    'organization_website': data['organization']['website_url'],
                    'organization_linkedin': data['organization']['linkedin_url'],
                    # 'organization_facebook': data['organization']['facebook_url'],
                    'organization_primary_phone': str(data['organization']['primary_phone']),
                    'organization_logo': data['organization']['logo_url'],
                    'organization_primary_domain': data['organization']['primary_domain'],
                    'organization_industry': data['organization']['industry'],
                    'organization_estimated_num_employees': str(data['organization']['estimated_num_employees']),
                    'organization_phone': data['organization']['phone'],
                    'organization_city': data['organization']['city'],
                    'organization_state': data['organization']['state'],
                    'organization_country': data['organization']['country'],
                    'organization_short_description': data['organization']['short_description'],
                    'organization_technology_names': str(data['organization']['technology_names'])
            }
            export_to_airtable(data_dict)
            print(f"\n------------Data ingestion successful for record id :{test_run_id}------------")
            response=fetch_and_update_data()
            print(response)
            print('\n------------ Data Cleaning Completed: Data Ready for Outreach ------------\n')
            return True
        else:
            print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
            return False
    
    except Exception as e:
        execute_error_block(f"Error occured during test run. {e}")

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
        # organization_num_employees_ranges=[value for value in organization_num_employees_ranges.split('],[')]
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
    return {'Status':f'Successfully enriched {success_status} profiles'} if success_status else {'Status':'No profiles enriched.'}
  except Exception as e:
    execute_error_block(f"Error occured while parsing the input. {e}")

if __name__ == '__main__':
  app.run(debug=True)
 