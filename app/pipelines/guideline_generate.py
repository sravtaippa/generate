import openai
from openai import OpenAI
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
import pinecone
from openai import OpenAI
import json
from ai_modules.generate_guideline import generator_guideline
from db.db_utils import retrieve_record,fetch_client_details,parse_people_info,unique_key_check_airtable,export_to_airtable,retrieve_client_tables,fetch_client_outreach_mappings,fetch_client_column

openai.api_key = OPENAI_API_KEY

def execute_generate_sequence():
    try:
        lead_info = retrieve_record("outreach_testing","apollo_id","66efc60fea68a2000105d5e0")
        generator_guideline.lead_info = lead_info.get('fields')
        # print(f"\n Lead info: {generator_guideline.lead_info}\n")
        generator_guideline.industry_type = generator_guideline.classify_company_vertical()
        print(f"\n-------------------------Industry type--------------------------------\n {generator_guideline.industry_type}\n")
        generator_guideline.person_research_data = generator_guideline.get_recent_achievements_person()
        print(f"\n------------------------ Person research data --------------------------------\n {generator_guideline.person_research_data}\n")
        generator_guideline.company_research_data = generator_guideline.get_recent_achievements_company()
        print(f"\n------------------------ Company research data ---------------------------------\n {generator_guideline.company_research_data}\n")

        if generator_guideline.industry_type in ["advertising_agencies"]:
            generator_guideline.search_term_cvp = generator_guideline.generate_search_term_cvp_agencies()
        elif generator_guideline.industry_type in ["brands","media_companies"]:
            generator_guideline.search_term_cvp = generator_guideline.generate_search_term_cvp_data_media()
        else:
            generator_guideline.search_term_cvp = generator_guideline.generate_search_term_cvp_data_media()
        
        print(f"\n---------------------- Client Value Proposition Search Term ----------------------------------\n {generator_guideline.search_term_cvp}\n")
        query_vector_cvp = generator_guideline.create_embedding_from_response_text(generator_guideline.search_term_cvp)
        # print(query_vector_cvp)
        generator_guideline.cvp_knowledge_base = generator_guideline.query_top_k_from_pinecone(
            query_vector=query_vector_cvp,
            top_k=10,
            namespace="",
            include_metadata=True)
        
        print(f"\n---------------------- Client Value Proposition ----------------------------------\n {generator_guideline.cvp_knowledge_base}\n")
        generator_guideline.search_term_pain_points = generator_guideline.generate_customer_pain_point_term()
        print(f"\n---------------------- Client Pain Points Search Term ----------------------------------\n {generator_guideline.search_term_pain_points}\n")
        query_vector_pain_points = generator_guideline.create_embedding_from_response_text(generator_guideline.search_term_pain_points)
        # print(query_vector_pain_points)
        generator_guideline.pain_points_knowledge_base = generator_guideline.query_top_k_from_pinecone(
            query_vector=query_vector_pain_points,
            top_k=10,
            namespace="",
            include_metadata=True)

        print(f"\n---------------------- Client Pain Points ----------------------------------\n {generator_guideline.pain_points_knowledge_base}\n")

    except Exception as e:
        print(f"Error occured at {__name__} while executing the generate sequence: {e}")
        return False