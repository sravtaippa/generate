import openai
import time
import json
import os
import json
import requests
from db.db_utils import unique_key_check_airtable,export_to_airtable,update_client_info,fetch_client_column
from pipelines.lead_website_analysis import analyze_website

from config import APOLLO_HEADERS

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")
CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")

def construct_query_param_range(key, values):
    print("&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values]))
    return "&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values])

def construct_query_param_keywords(key, value):
    return f"{key}={value.replace(',', '%2C').replace(' ','%20')}"

def construct_query_param(key, values):
    res = "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])
    print(res)
    return "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])

def lowercase_keys(json_data, keys_to_lowercase):
    for key in keys_to_lowercase:
        if key in json_data and isinstance(json_data[key], list):
            json_data[key] = [value.lower() for value in json_data[key] if isinstance(value, str)]
    return json_data

def generate_icp(client_id,website_url):
    try:
        print(f"\n\n--------Generating ICP --------\n\n")
        openai.api_key = OPENAI_API_KEY
        explicit_icp_criteria = fetch_client_column(CLIENT_INFO_TABLE_NAME,client_id,"explicit_icp_criteria")
        print(f"explicit_icp_criteria : {explicit_icp_criteria}")
        icp_description, icp_apollo_tags, value_proposition_details = analyze_website(website_url,explicit_icp_criteria)
        print(f"\n\n----ICP Description retrieved: {icp_description}------\n\n")
        print(f"\n\n----ICP Apollo Tags retrieved: {icp_apollo_tags}------\n\n")
        print(f"\n\n----Client Value Proposition retrieved: {value_proposition_details}------\n\n")
        parsed_json = json.loads(icp_apollo_tags)
        print(parsed_json)
        keys_to_lowercase = ["job_titles", "person_seniorities", "person_locations"]
        # Convert values to lowercase
        icp_json = lowercase_keys(parsed_json, keys_to_lowercase)
        print(f"Updated json: {icp_json}")
        print(f"Completed creating ICP json")
        results_per_page=100
        person_titles = icp_json.get('job_titles') 
        person_seniorities = icp_json.get('person_seniorities')
        person_locations = icp_json.get('person_locations')
        email_status = ['verified']
        organization_num_employees_ranges = icp_json.get('employee_range')
        print(f"\n\n--------Creating query params--------\n\n")
        query_params = [
                    construct_query_param("person_titles", person_titles),
                    construct_query_param("person_seniorities", person_seniorities),
                    construct_query_param("person_locations", person_locations),
                    construct_query_param("organization_locations", person_locations),
                    construct_query_param("contact_email_status", email_status),
                    construct_query_param_range("organization_num_employees_ranges", organization_num_employees_ranges),
        ]
        query_params_test = query_params.copy()
        query_params_test.append("page=1")
        query_params.append("page={page_number}")
        query_params.append("per_page={records_required}")
        query_params_test.append(f"per_page={results_per_page}")
        base_url = "https://api.apollo.io/api/v1/mixed_people/search"
        url_test = f"{base_url}?{'&'.join(query_params_test)}"
        dynamic_url = f"{base_url}?{'&'.join(query_params)}"
        headers = APOLLO_HEADERS
        print(f"Updating the value proposition details for the client")
        update_client_info(CLIENT_INFO_TABLE_NAME,client_id,value_proposition_details)
        print(f"Successfully updated value proposition details for the client")
        print(f"\n\nRunning the people search API test")
        print(f"\n\n------------Apollo Url for testing : {url_test}------------------------")
        response = requests.post(url_test, headers=headers)
        if response.status_code == 200:
            print(f"\n------------Completed Persona Data Mining------------")
            data = response.json()
            print(f"No of profiles collected : {len(data['people'])}")
            record_exists = unique_key_check_airtable('client_id',client_id,CLIENT_CONFIG_TABLE_NAME)
            if record_exists:
                print(f'Record with the following id: {client_id} already exists for client config table. Skipping the entry...')
                return True
            config_data = {
                "client_id":client_id,
                "icp_url":dynamic_url,
                "icp_description":icp_description,
                "icp_job_details":str(person_titles),
                "icp_job_seniorities":str(person_seniorities),
                "icp_employee_range":str(organization_num_employees_ranges),
                "icp_locations":str(person_locations),
                "page_number":'1',
                "qualify_leads":'no',
                "records_required":'5',
                "is_active":"yes",
            }
            export_to_airtable(config_data, CLIENT_CONFIG_TABLE_NAME)
        return dynamic_url
    
    except Exception as e:
        print(f"Error occured at {__name__} while generating icp: {e}")
        return False

if __name__=="__main__":
    pass