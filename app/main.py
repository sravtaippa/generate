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
from pipelines.data_extractor import people_enrichment,test_run_pipeline,run_demo_pipeline
from db.table_creation import create_client_tables
from pipelines.icp_generation import generate_icp
from db.db_utils import fetch_client_details,export_to_airtable,unique_key_check_airtable,parse_people_info,add_client_tables_info
from error_logger import execute_error_block
from lead_magnet.lead_magnet_pdf_generation import generate_lead_magnet_pdf
from pipelines.data_sync import trigger_pipeline
from pipelines.lead_website_analysis import chroma_db_testing
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
        print(f"\n\n------------- Client Onboarding Process Started for client_id-----------------\n\n")
        client_id = request.args.get('client_id', type=str)
        website_url = request.args.get('website_url', type=str)
        if client_id in ["",None] or website_url in ["",None]:
            print(f"Invalid information passed. client_id : {client_id}, website_url: {website_url}")
            return {"Status":f"Invalid information passed. client_id : {client_id}, website_url: {website_url}"}
        print(f"Fetched parameters-> client_id : {client_id}, website_url : {website_url}")
        src_table, cur_table, outreach_table = create_client_tables(client_id)
        print(f"------ Client tables created for client_id : {client_id} -------------")
        add_client_tables_info(client_id,src_table,cur_table,outreach_table)
        print(f"------ Added client tables info to the airtable for client_id : {client_id} -------------")
        status = generate_icp(client_id,website_url)
        print(f"------ Successfully generated ICP and Client value proposition for the client: {client_id} -------------")
        print("\n\n--------Started Data Sync ---------\n\n")
        trigger_pipeline()
        print("\n\n--------Completed Data Sync ---------\n\n")
        print("Client onboarding successful")
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
        status = trigger_pipeline()
        return {"Status":"Successful"}
        # response=fetch_and_update_data(client_id)
        # return {"Status":"Testing sanitization successful"}
    except Exception as e:
        print(f"Exception occured during scheduled data sync: {e}")
        execute_error_block(f"Exception occured during scheduled data sync: {e}")

if __name__ == '__main__':
  app.run(debug=True,use_reloader=False)
 