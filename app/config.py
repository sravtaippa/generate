import os 

print(f"\n--------------- Retrieving the Secret keys ---------------")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

CLIENT_DETAILS_TABLE_NAME = os.getenv("CLIENT_DETAILS_TABLE_NAME")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")

APOLLO_HEADERS = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY
        }

print(f"AIRTABLE_API_KEY: {AIRTABLE_API_KEY}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"APOLLO_API_KEY: {APOLLO_API_KEY}")
print(f"AIRTABLE_BASE_ID: {AIRTABLE_BASE_ID}")
print(f"AIRTABLE_TABLE_NAME: {AIRTABLE_TABLE_NAME}")
print(f"PERPLEXITY_API_KEY: {PERPLEXITY_API_KEY}")
print(f"APIFY_API_TOKEN: {APIFY_API_TOKEN}")
print(f"CLIENT_DETAILS_TABLE_NAME: {CLIENT_DETAILS_TABLE_NAME}")
print(f"CLIENT_INFO_TABLE_NAME: {CLIENT_INFO_TABLE_NAME}")
print(f"CLIENT_CONFIG_TABLE_NAME: {CLIENT_CONFIG_TABLE_NAME}")
print(f"\n----------------------------------------------------------")
