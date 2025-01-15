import requests
import openai

from db.db_utils import fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable
from pipelines.lead_qualifier import qualify_lead
from error_logger import execute_error_block
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS
from lead_magnet.industry_insights import get_cold_email_kpis

def people_enrichment(apollo_id):
    try:
        print(f"\n------------Started Persona Data Enrichment------------")
        url = f"https://api.apollo.io/api/v1/people/match?id={apollo_id}&reveal_personal_emails=false&reveal_phone_number=false"
        response = requests.post(url, headers=APOLLO_HEADERS)
        # print(response.json())
        print(f"------------Completed Persona Data Enrichment------------")
        return response
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} for the data enrichment layer. {e}")

def people_search(query_params,client_id,qualify_leads):
  try:
    print(f"\n------------Started Persona Data Mining------------")
    base_url = "https://api.apollo.io/api/v1/mixed_people/search"
    url = f"{base_url}?{'&'.join(query_params)}"
    print(url)  
    response = requests.post(url, headers=APOLLO_HEADERS)
    print(f"Execution status code: {response.status_code}")
    if response.status_code == 200:
        print(f"\n------------Completed Persona Data Mining------------")
        data = response.json()
        print(f"No of profiles collected : {len(data['people'])}")
        # return str(len(data['people']))
        profiles_found = len(data['people'])
        enriched_profiles=0
        selected_profiles=0
        if qualify_leads=='yes':
            solution_benefits,unique_features,solution_impact_examples,domain,buyer_criteria,buyer_examples = fetch_client_details(client_id)
        print(f"\n------------Initiating Persona Data Fetch Iteration------------")
        for contact in data['people']:
            apollo_id = contact['id']
            unique_value = apollo_id
            persona_details=parse_people_info(contact)
            if qualify_leads=='yes':
                qualification_status = qualify_lead(
                    persona_details=persona_details,
                    solution_benefits=solution_benefits,
                    unique_features=unique_features,
                    solution_impact_examples=solution_impact_examples,
                    domain=domain,
                    buyer_criteria=buyer_criteria,
                    buyer_examples=buyer_examples
                    )
                # qualification_status_test = qualify_lead_test(
                #     persona_details=persona_details,
                #     solution_benefits=solution_benefits,
                #     unique_features=unique_features,
                #     solution_impact_examples=solution_impact_examples,
                #     domain=domain,
                #     buyer_criteria=buyer_criteria,
                #     buyer_examples=buyer_examples
                #     )
                # continue
                if not qualification_status:
                    print(f"\n------------Lead Disqualified------------")
                    print('Skipping the entry...')
                    continue
                print(f"\n------------Lead Qualified------------")
            else:
                print(f"Skipping lead qualification...")
            print(f"\n------------Data ingestion started for record id :{apollo_id}------------")
            record_exists = unique_key_check_airtable('id',apollo_id)   
            if record_exists:
                print(f'Record with the following id: {apollo_id} already exists. Skipping the entry...')
                continue   
            
            enrichment_api_response = people_enrichment(apollo_id)
            enriched_profiles+=1
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
                    'email': data['email'],
                    'linkedin_url': data['linkedin_url'],
                    'associated_client_id': client_id,
                    'title': data['title'],
                    'seniority': data['seniority'],
                    'headline': data['headline'],
                    # 'is_likely_to_engage': str(data['is_likely_to_engage']),
                    'is_likely_to_engage': 'True',
                    'photo_url': data['photo_url'],
                    'email_status': contact['email_status'],
                    'twitter_url': data['twitter_url'],
                    'github_url': data['github_url'],
                    'facebook_url': data['facebook_url'],
                    'employment_history': str(data['employment_history']),
                    'employment_summary':str(employment_summary),
                    'organization_name': data['organization']['name'],
                    'organization_website': data['organization']['website_url'],
                    'organization_linkedin': data['organization']['linkedin_url'],
                    'organization_facebook': data['organization']['facebook_url'],
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
                selected_profiles+=1
                print(f"\n------------Data ingestion successful for record id :{apollo_id}------------")
            else:
                print(f"Error: {enrichment_api_response.status_code}, People Enrichment API failed")
                return False
        print('\n------------ Completed Data Collection, Initiating Data Cleaning------------\n')
        print(f"Total profiles found: {profiles_found}")
        print(f"Total profiles enriched: {enriched_profiles}")
        print(f"Total profiles uploaded: {selected_profiles}")
        return selected_profiles  
    else:
        print(f"\n------------ ERROR : Persona Search API Failed ------------")
        return False
  except Exception as e:
    execute_error_block(f"Error occured in {__name__} during data ingestion. {e}")