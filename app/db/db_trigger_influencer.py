import os
import time
from datetime import datetime
import datetime as dt
import openai
import requests
from error_logger import execute_error_block
from db.db_ops import db_manager
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS,PERPLEXITY_API_KEY


def influencer_table_trigger(campaign_id,social_media_type):
    try:
        campaign_id = "taippa"
        influencer_table = "influencer_profile_urls"
        profile_checkpoint_table = "social_media_profile_checkpoint"
        query = ""
        if social_media_type.upper() == "INSTAGRAM":
            checkpoint_column_name= "last_processed_time_instagram"
            data_fetch_query = f"""SELECT *
                        FROM {influencer_table}
                        WHERE created_time > (
                            SELECT last_processed_time_instagram
                            FROM {profile_checkpoint_table}
                            WHERE campaign_id = '{campaign_id}') and social_media_type = 'instagram' LIMIT 3;
                    """
        elif social_media_type.upper() == "TIKTOK":
            checkpoint_column_name= "last_processed_time_tiktok"
            data_fetch_query = f"""SELECT *
                        FROM {influencer_table}
                        WHERE created_time > (
                            SELECT last_processed_time_tiktok
                            FROM {profile_checkpoint_table}
                            WHERE campaign_id = '{campaign_id}') and social_media_type = 'tiktok' LIMIT 3;
                    """
           
        if data_fetch_query:
            data = db_manager.get_records_from_query_v2(data_fetch_query)
            print(data)
            if not data:
                print(f"No data found")
                max_created_time = None  # or default datetime if you want
            else:
                max_created_time = max(item['created_time'] for item in data)

            if max_created_time:
                checkpoint_update_query = f"""UPDATE {profile_checkpoint_table}
                            SET {checkpoint_column_name} = '{max_created_time}'
                            WHERE campaign_id = '{campaign_id}';
                    """
                db_manager.get_records_from_query_v2(checkpoint_update_query)
                print(f"Updated table status successfully")
            return data
        else:
            print(f"Invalid social media type passed: {social_media_type}")
            return []
    except Exception as e:
        print(f"Error occured while executing influencer table trigger")
        return []
    
def export_influencer_data(influencer_data):
    try:
        tiktok_url = influencer_data.get("tiktok_username")
        influencer_table = "src_influencer_data"
        if tiktok_url != "NA" or tiktok_url != "":
            data_fetch_query = f"""select id from {influencer_table} where 
                        tiktok_username = {tiktok_url} LIMIT 1;
                    """
            data = db_manager.get_records_from_query_v2(data_fetch_query)
            if data:
                id = data.get("id")
                update_fields = {"id":id} | influencer_data
                db_manager.update_multiple_fields(influencer_table, update_fields, id)
                print(f"Influencer record updated successfully")
        else:
            db_manager.insert_data(influencer_data,"src_influencer_data")
            print("Influencer record added to db")

    except Exception as e:
        print(f"Error occured while ingesting influencer data: {e}")