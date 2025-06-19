import os
import time
import openai
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
from db.db_ops import db_manager

def retrieve_data_from_db(sql_query):
    try:
        print(f"Executing SQL query: {sql_query}")
        results = db_manager.get_records_from_query(sql_query)
        print("SQL query executed successfully.")
        print(results)
        return results
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None