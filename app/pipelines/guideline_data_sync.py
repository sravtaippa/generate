import requests
import urllib.parse
import openai
import os
from datetime import datetime
from pipelines.data_sanitization import sanitize_data
from db.db_utils import fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,get_clients_config,fetch_page_config,update_client_config,phone_number_updation,fetch_client_column,get_source_data,update_column_value,retrieve_record
from error_logger import execute_error_block
from pipelines.data_extractor import people_search_v2,manual_data_insertion
from pipelines.icp_generation import generate_apollo_url
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
import pandas as pd

# from lead_magnet.industry_insights import get_cold_email_kpis
 
CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")

contacts = {
    "PubMatic": "Robin Steinberg",
    "Amazon Ads": "David Grossman",
    "Nielsen": "Darina Lyons",
    "The Channel Factory": ["Andreia Todd", "Philip Cowdell"],
    "TransUnion": "Andrea Ferguson",
    "Emodo": ["Alistair Goodman", "Damian McKenna"],
    "Zeta Global": "Courtney Greenberg",
    "Agnitio.io": "Aubriana Lopez",
    "Wild Brain Media Solutions": "Emma Witkowski",
    "Reddit": "Susan Billingsley",
    "Premion": "Peter Jones",
    "Start.io": "Omer Peled",
    "Innovid": "Chris Klein",
    "Swoop": "Nicole Miller",
    "Viant": ["Erin Donohoe", "Amanda Sheplee"],
    "Craft & Commerce": "Mark Baker",
    "Activision Blizzard Media": "Kelly Drake",
    "Acxiom/Kinesso": "Elizabeth Donovan",
    "AdMedia": "Jeff Alderman",
    "Adobe": "Heather Freeland",
    "Adobe Incorporated": "Allison Blais",
    "Align Technology": "Kamal Bhandal",
    "Aperiam.vc": "Eric Franchi",
    "Arity": "Fred Dimesa",
    "BMW North America": "Marcus Casey",
    "Clinch": "Oz Etzioni",
    "CMI Media Group": "Justin Freid",
    "CONVERSATE COLLECTIVE LLC": "Aja Bradley Kemp",
    "CVS Pharmacy": "Erin Condon",
    "CVS Pharmacy, Inc. (CVS Health)": "Melissa Gallo",
    "Dailymotion": "Sean Black",
    "Deep Blue Sports and Entertainment": "Laura Correnti",
    "Digital Turbine": "Michael Akkerman",
    "DISH Media": "Tom Fochetta",
    "Disney Advertising": "Matt Barnes",
    "DPAA": "Barry Frey",
    "General Motors": "Norm de Greve",
    "Google": "Scott Falzone",
    "Growth Channel": "Maryna Burushkina",
    "HP Inc.": "Scott Decker",
    "Influential": ["Chris Detert", "Ryan Detert"],
    "Intent IQ": "Fabrice Beer-Gabel",
    "Intuit": ["Meg Beaudet", "Mike Denzler"],
    "iSpot": "Alex Freed",
    "Jones Road": "Bobbi Brown",
    "Kellanova": "Julie Bowerman",
    "Lenovo": "Kate Clough",
    "Microsoft Advertising": "Greg Carroll",
    "Molson Coors Beverage Company": "Brad Feinberg",
    "National Football League (NFL)": "Tim Ellis",
    "Popeyes Louisiana Kitchen": "Jean Paul Ciaramella",
    "Roundel, Target": "Matt Drzewicki",
    "Sabio": "Liz Blacker",
    "She Runs It": "Lynn Branigan",
    "Shutterstock": ["Aiden Darné", "Aimee Egan"],
    "SiriusXM Media": "Antonio Francisco",
    "TCS Interactive": "Andrew Essex",
    "The Drum": "Jenni Baker",
    "TikTok": "Lorry Destainville",
    "Translation United Masters": "Chaucer Barnes",
    "TripleLift": ["RC Casey", "Ed Dinichert"],
    "True Religion": "Kristen D'Arcy",
    "Unilever": "Esi Eggleston Bracey",
    "United Talent Agency": "Ziad Ahmed",
    "VaynerX": "Avery Akkineni",
    "VISA": "Frank Cooper II",
    "Walmart Inc.": "John Furner",
    "Wpromote": "Darren D'Altorio",
    "Wurl": "Pete Crofut"
}

excluded_profiles = []
def data_enrich(name,organization):
    try:
        query_params=[]
        encoded_name = urllib.parse.quote(name)
        query_params.append(f"name={encoded_name}")
        query_params.append(f"organization_name={organization}")
        query_params.append("reveal_personal_emails=false")
        query_params.append("reveal_phone_number=false")
        base_url = "https://api.apollo.io/api/v1/people/match"
        dynamic_url = f"{base_url}?{'&'.join(query_params)}"
        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": "ti7hoaAD9sOc5DGzqZUk-Q"
        }
        # print(dynamic_url)
        response = requests.post(dynamic_url, headers=headers)
        data = response.json()
        # print(data)
        return data['person'] if data else None
    except Exception as e:
       execute_error_block(f"Error occured while enriching the data {e}")

def parse_record(data,organization):
    try:
        if data.get("linkedin_url") is None or data.get("email") is None:
            print(f"Skipping the record as the linkedin_url or email is not available")
            excluded_profiles.append(organization)
            return None
        client_id = "cl_possible_event"
        # print(f"Parsing the record: {data}")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
        model="gpt-4",
        messages=[
                    {"role": "system", "content": "You are an expert at text summarization."},
                    {"role": "user", "content": f"Please shorten this description: {data['employment_history']}"}
        ],
        )
        employment_summary = response.choices[0].message.content
        timestamp = datetime.now()
        return  {
                    'apollo_id': data.get('id'),
                    'first_name': data.get('first_name'),
                    'last_name': data.get('last_name'),
                    'name': data.get('name'),
                    'email': data.get('email'),
                    'linkedin_url': data.get('linkedin_url'),
                    'associated_client_id': client_id,
                    'title': data.get('title'),
                    'seniority': data.get('seniority'),
                    'headline': data.get('headline'),
                    'is_likely_to_engage': 'True',
                    'photo_url': data.get('photo_url'),
                    'email_status': data.get('email_status'),
                    'twitter_url': data.get('twitter_url'),
                    'github_url': data.get('github_url'),
                    'facebook_url': data.get('facebook_url'),
                    'employment_history': str(data.get('employment_history')),
                    'employment_summary':str(employment_summary),
                    'organization_name': data.get('organization').get('name'),
                    'organization_website': data.get('organization').get('website_url') if data.get('organization') else '',
                    'organization_linkedin': data.get('organization').get('linkedin_url') if data.get('organization') else '',
                    'organization_facebook': data.get('organization').get('facebook_url') if data.get('organization') else '',
                    'organization_primary_phone': str(data.get('organization').get('primary_phone')) if data.get('organization') else '',
                    'organization_logo': data.get('organization').get('logo_url') if data.get('organization') else '',
                    'organization_primary_domain': data.get('organization').get('primary_domain') if data.get('organization') else '',
                    'organization_industry': data.get('organization').get('industry') if data.get('organization') else '',
                    'organization_estimated_num_employees': str(data.get('organization').get('estimated_num_employees')) if data.get('organization') else '',
                    'organization_phone': data.get('organization').get('phone') if data.get('organization') else '',
                    'organization_city': data.get('organization').get('city') if data.get('organization') else '',
                    'organization_state': data.get('organization').get('state') if data.get('organization') else '',
                    'organization_country': data.get('organization').get('country') if data.get('organization') else '',
                    'organization_short_description': data.get('organization').get('short_description') if data.get('organization') else '',
                    'organization_technology_names': str(data.get('organization').get('technology_names')) if data.get('organization') else '',
                    'created_time':str(timestamp),
                    'filter_criteria':"specific"
                }
    except Exception as e:
        execute_error_block(f"Error occured while parsing the record: {e}")
        
def parse_contacts():
    try:
        itr=1
        for contact in contacts:
            print(itr)
            itr+=1
            organization = contact
            profiles= contacts[contact]
            raw_table = "src_cl_possible_event"
            if isinstance(profiles, list):
                for profile_name in profiles:
                    record = data_enrich(profile_name,organization)
                    if record is not None:
                        print('testing unique check')
                        apollo_id = record.get('apollo_id')
                        record_exists = unique_key_check_airtable('apollo_id',apollo_id,raw_table)
                        if record_exists:
                            print(f'Record with the following id: {apollo_id} already exists. Skipping the entry...')
                            continue
                        record['filter_criteria']="specific" 
                        parsed_record = parse_record(record,organization) 
                        if parsed_record:
                            export_to_airtable(parsed_record,raw_table)
                            sanitize_data("cl_possible_event",parsed_record)
            else:
                profile_name = profiles
                record = data_enrich(profile_name,organization)
                if record is not None:
                    print('testing unique check')
                    apollo_id = record.get('apollo_id')
                    record_exists = unique_key_check_airtable('apollo_id',apollo_id,raw_table)   
                    if record_exists:
                        print(f'Record with the following id: {apollo_id} already exists. Skipping the entry...')
                        continue 
                    record['filter_criteria']="specific"
                    parsed_record = parse_record(record,organization)
                    if parsed_record:
                            export_to_airtable(parsed_record,raw_table)
                            sanitize_data("cl_possible_event",parsed_record) 
        print("Excluded profiles: ",excluded_profiles)
    except Exception as e:
        execute_error_block(f"Error occured while parsing the contacts: {e}")


# from pyairtable import Table,Api

# def data_enrich(first_name,last_name,organization):
#   query_params=[]
#   query_params.append(f"first_name={first_name}")
#   query_params.append(f"last_name={last_name}")
#   encoded_organization = urllib.parse.quote(organization)
#   query_params.append(f"organization_name={encoded_organization}")
#   query_params.append("reveal_personal_emails=true")
#   query_params.append("reveal_phone_number=false")
#   base_url = "https://api.apollo.io/api/v1/people/match"
#   dynamic_url = f"{base_url}?{'&'.join(query_params)}"
#   headers = {
#       "accept": "application/json",
#       "Cache-Control": "no-cache",
#       "Content-Type": "application/json",
#       "x-api-key": "ti7hoaAD9sOc5DGzqZUk-Q"
#   }
#   # print(dynamic_url)
#   response = requests.post(dynamic_url, headers=headers)
#   data = response.json()
#   print(data)
#   return data['person'] if data else None

# def export_to_airtable(data,raw_table):
#     try:
#         # print(f"\nExporting results to Airtable")
#         api = Api("patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3")
#         airtable_obj = api.table("app5s8zl7DsUaDmtx", raw_table)
#         response = airtable_obj.create(data)
#         if 'id' in response:
#             print("Record inserted successfully:", response['id'])
#         else:
#             print("Error inserting record:", response)
#     except Exception as e:
#         print(f"Error occured in {__name__} while exporting the data to Airtable. {e}")

# def unique_key_check_airtable(column_name,unique_value,table_name):
#     try:
#         api = Api("patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3")
#         airtable_obj = api.table('app5s8zl7DsUaDmtx', table_name)
#         records = airtable_obj.all()
#         # print(f"\nCompleted unique key check")
#         return any(record['fields'].get(column_name) == unique_value for record in records) 
#     except Exception as e:
#       print(f"error occured while unique key check {e}")


# # Read the Excel file
# df = pd.read_excel("/content/drive/MyDrive/Guideline/POSSIBLE Attendee List 3.4.xlsx")
# # len(df)
# # # Iterate through each row
# profiles = []
# final_list= []
# for index, row in df.iterrows():
#     if index < 591:
#       continue

#     print(f"======Index {index}===============")
#     info={}
#     first_name = row['First Name']
#     last_name = row['Last Name']
#     organization = row['Org Name']
#     data = data_enrich(first_name,last_name,organization)
#     if data is None:
#       continue
#     parsed_data = parse_record(data,organization)
#     if parsed_data is None:
#       continue
#     apollo_id = parsed_data['apollo_id']
#     record_exists = unique_key_check_airtable('apollo_id',apollo_id,"src_possible_event_updated_list")   
#     if record_exists:
#       print(f'Record with the following id: {apollo_id} already exists. Skipping the entry...')
#       continue    
#     profiles.append(parsed_data)
#     export_to_airtable(parsed_data,"src_possible_event_updated_list")
#     print(f"===============================")


if __name__ == "__main__":
    parse_contacts()
