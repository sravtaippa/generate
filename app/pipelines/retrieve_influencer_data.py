import os
import time
import openai
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
from db.db_ops import db_manager
from pyairtable import Table,Api



def store_filtered_data(data_list,brand_id,brand_brief):
    try:
        def unique_key_check_airtable(column_name,unique_value,table_name):
            try:
                api = Api(AIRTABLE_API_KEY)
                airtable_obj = api.table(AIRTABLE_BASE_ID, table_name)
                records = airtable_obj.all()
                # print(f"\nCompleted unique key check")
                return any(record['fields'].get(column_name) == unique_value for record in records) 
            except Exception as e:
                print(f"Error occured in {__name__} while performing unique value check in airtable. {e}")

        # function to export data to Airtable
        def export_to_airtable(data,raw_table):
            try:
                # print(f"\nExporting results to Airtable")
                api = Api(AIRTABLE_API_KEY)
                airtable_obj = api.table(AIRTABLE_BASE_ID, raw_table)
                response = airtable_obj.create(data)
                if 'id' in response:
                    print("Record inserted successfully:", response['id'])
                else:
                    print("Error inserting record:", response)
            except Exception as e:
                print(f"Error occured in {__name__} while exporting the data to Airtable. {e}")

        for data in data_list:
            print(f"Processing record: {data}")
            if data.get("instagram_url") is None:
                print(f"Skipping record as instagram_url is None")
                continue
            record_exists = unique_key_check_airtable('instagram_url',data["instagram_url"],"filtered_influencer_data")
            if not record_exists:
                print(f"Record doesn't exist")
                data["brand_id"] = brand_id
                data["brand_brief"] = brand_brief
                data["created_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                export_to_airtable(data,"filtered_influencer_data")
            else:
                print(f"Record Exists")

    except Exception as e:
        print(f"Error storing data: {e}")

def retrieve_data_from_db(sql_query,brand_id,brand_brief):
    try:
        print(f"Executing SQL query: {sql_query}")
        results = db_manager.get_records_from_query_v2(sql_query)
        print("SQL query executed successfully.")
        print(results)
        print(f"Storing filtered data to Airtable")
        store_filtered_data(results,brand_id,brand_brief)
        return results
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None
    
