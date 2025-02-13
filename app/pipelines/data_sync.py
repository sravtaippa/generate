import requests
import openai
import os
from datetime import datetime

from pipelines.data_sanitization import fetch_and_update_data
from db.db_utils import fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,get_clients_config,fetch_page_config,update_client_config
from pipelines.lead_qualifier import qualify_lead
from error_logger import execute_error_block
from pipelines.data_extractor import people_search_v2
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
# from lead_magnet.industry_insights import get_cold_email_kpis
 
CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")

def trigger_pipeline():
    try:
        config_data = get_clients_config(CLIENT_CONFIG_TABLE_NAME)
        print("\n================= Scheduled Pipeline Execution Started ==========================================\n")
        for client_config in config_data:
            try:
                client_details = client_config.get('fields')
                client_id = client_details.get('client_id')
                qualify_leads = client_details.get('qualify_leads')
                last_page,records_required,active_status = fetch_page_config(CLIENT_CONFIG_TABLE_NAME,client_id)
                print(f"\n-------------------- Data Sync started for Client : {client_id} ------------------------\n") 
                if not active_status or active_status.upper() == 'NO':
                    print(f"Skipping data sync since the entry is not active")
                    print(f"\n-------------------- Data Sync Skipped for Client : {client_id}------------------------\n")
                    continue
                print(client_details.get('icp_url'))
                print(f"Formatting the dynamic url for Apollo search")
                icp_url = client_details.get('icp_url').format(page_number=last_page,records_required=records_required)
                print(f" Apollo Search Url : {icp_url}")
                profiles_enriched = people_search_v2(icp_url,client_id,qualify_leads)
                print(f"Profiles Enriched : {profiles_enriched}")
                response=fetch_and_update_data(client_id)
                print(response)
                print(f"\n------------ Data populated for the outreach table for the client_id: {client_id}\n")
                updated_status = update_client_config(CLIENT_CONFIG_TABLE_NAME,client_id,profiles_enriched)
                print(f"\n-------------------- Data Sync completed for Client : {client_id}------------------------\n") 
            except Exception as e:
                print(f"Error occured during data sync for client.{e}")
        print("\n================= Scheduled Pipeline Execution Completed ==========================================\n")
        return config_data
    except Exception as e:
        execute_error_block(f"Exception occured while triggering the pipeline run {e}")
