from pyairtable import Table,Api
import openai
from error_logger import execute_error_block
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,PERPLEXITY_API_KEY

def retrieve_client_tables(client_id):
    try:
        print('Retreiving tables')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, "client_details")
        records = airtable_obj.all()
        print(f"\nRan the client details fetch command")
        record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        # print(record_details) 
        raw_table = record_details.get('fields').get('raw_table')
        cleaned_table = record_details.get('fields').get('cleaned_table')
        outreach_table = record_details.get('fields').get('outreach_table')
        return raw_table,cleaned_table,outreach_table
    except Exception as e:
        print(f"Error occured in {__name__} while retrieving tables from airtable. {e}")


def fetch_client_outreach_mappings(client_id):
    try:
        print(f"\nFetching details for outreach mapping")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, "client_details")
        record = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0].get('fields')
        return {
            "email": record.get("email"),
            "company_name": record.get("company_name"),
            "full_name": record.get("full_name"),
            "job_title": record.get("job_title"),
            "company_website": record.get("company_website"),
            "solution_benefits": record.get("solution_benefits"),
            "solution_impact_examples": record.get("solution_impact_examples"),
            "unique_features": record.get("unique_features"),
            "cta_options": record.get("cta_options"),
            "color_scheme": record.get("color_scheme"),
            "font_style": record.get("font_style"),
            "instantly_campaign_id": record.get("instantly_campaign_id"),
            "business_type": record.get("business_type"),
            "outreach_table": record.get("outreach_table")
        }
    
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client mappings. {e}")

def fetch_client_details(client_id):
    try:
        print(f"\nFetching Client Details")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, "client_details")
        record = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        solution_benefits = record['fields']['solution_benefits']
        unique_features = record['fields']['unique_features']
        solution_impact_examples = record['fields']['solution_impact_examples']
        domain = record['fields']['domain']
        buyer_criteria = record['fields']['buyer_criteria']
        buyer_examples = record['fields']['buyer_examples']
        print(f"\nSuccessfully fetched client details")
        return solution_benefits,unique_features,solution_impact_examples,domain,buyer_criteria,buyer_examples
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client details. {e}")

def get_clients_config(client_config_table):
    try:
        print('Fetching clients list from config table')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        config_data = airtable_obj.all()
        # data_count = len(airtable_obj.all())
        # print(data_count)
        # print(f"Length of the list: {data_count}")
        # record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        # page_number = record_details.get('fields').get('page_number')
        return config_data
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching client config details. {e}")

def fetch_latest_page_number(client_config_table,client_id):
    try:
        print('Fetching latest page number')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, client_config_table)
        print(f"\n Fetching latest page number from the table")
        data_count = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")
        record_details = airtable_obj.all(formula=f"{{client_id}} = '{client_id}'")[0]
        page_number = record_details.get('fields').get('page_number')
        return page_number
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while fetching latest page number. {e}")

# function to export data to Airtable
def export_to_airtable(data,raw_table):
    try:
        print(f"\nExporting results to Airtable")
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
        response = airtable_obj.create(data)
        # Check if the insertion was successful
        if 'id' in response:
            print("Record inserted successfully:", response['id'])
        else:
            print("Error inserting record:", response)
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while exporting the data to Airtable. {e}")

def unique_key_check_airtable(column_name,unique_value,raw_table):
    try:
        print('Running unique key check')
        api = Api(AIRTABLE_API_KEY)
        airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
        records = airtable_obj.all()
        print(f"\nCompleted unique key check")
        return any(record['fields'].get(column_name) == unique_value for record in records) 
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while performing unique value check in airtable. {e}")

def parse_people_info(data):
    try:
        print('----------Parsing the data input --------------]')
        employment_history = data['employment_history']
        response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",  # or "gpt-4" for more advanced results
                        messages=[
                            {"role": "system", "content": "You are an expert at text summarization."},
                            {"role": "user", "content": f"Please summarize this description: {employment_history}"}
                        ],
                        max_tokens=100  # Adjust based on the desired length of the output
                        )
        employment_summary = response['choices'][0]['message']['content']
        parsed_people_info={
            "title":data.get('title'),
            "headline":data.get('headline'),
            "country":data.get('country'),
            "city":data.get('city'),
            "departments":data.get('departments'),
            "subdepartments":data.get('subdepartments'),
            "functions":data.get('functions'),
            "employment_summary":employment_summary
        }
        return parsed_people_info
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while parsing the data input. {e}")
