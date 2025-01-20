from pyairtable import Table,Api
import openai
from error_logger import execute_error_block
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

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
            "title":data['title'],
            "headline":data['headline'],
            "country":data['country'],
            "city":data['city'],
            "departments":data['departments'],
            "subdepartments":data['subdepartments'],
            "functions":data['functions'],
            "employment_summary":employment_summary
        }
        return parsed_people_info
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while parsing the data input. {e}")
