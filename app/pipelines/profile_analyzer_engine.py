import openai
import json
import os

from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

openai.api_key =  OPENAI_API_KEY 



def classify_vertical(instagram_bio, influencer_location, trimmed_instagram_caption, trimmed_instagram_hashtags):
    try:

        # Define system + user messages
        system_prompt = """
        You are a smart assistant programmed to analyze social media profiles of users. Based on the provided information, classify the user into the following categories and return a valid JSON string as output.

        - The "targeted_domain" must be one of: ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"].
        - The "targeted_audience" must be one of: ["gen-z", "gen-y", "gen-x"], based on user's age or inferred clues. Use:
        - gen-z: born between 1997–2012
        - gen-y: born between 1981–1996
        - gen-x: born between 1965–1980
        - The "influencer_nationality" should be inferred from the bio and current location if possible. If not clear, set to "unknown".

        Always return a JSON string object ONLY like this:
        {
        "influencer_nationality": "",
        "targeted_audience": "",
        "targeted_domain": ""
        }
        """

        user_prompt = f"""
        These are the available details:

        bio of user: {instagram_bio}
        current_location of user: {influencer_location}

        trimmed captions used for different posts in instagram: {trimmed_instagram_caption}

        trimmed instagram hashtags for different posts:
        {trimmed_instagram_hashtags}

        Please analyze and classify the profile based on the above criteria and return a JSON object.
        """

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # You can use "gpt-3.5-turbo" if needed
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.2
        )

        # Extract the response
        result = response['choices'][0]['message']['content'].strip()

        # Validate it's a JSON string (not markdown-formatted)
        try:
            parsed = json.loads(result)
            print("Classification Result:")
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print("The response is not a valid JSON string. Here's the raw output:")
            print(result)

    except Exception as e:
        print(f" Error during classification: {e}")


def classify_profile_type(instagram_bio,business_category_name):
    try:
        # Define the system and user prompts
        system_prompt = """
        You are a smart assistant programmed to analyze social media profiles and determine whether the profile belongs to an individual or a group/team.

        Possible profile types:
        - person
        - group

        Your task is to return only one of the above tags, and nothing else.
        """

        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, business_category_name: {business_category_name}
        """

        # Send request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or use "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract the classification
        profile_type = response['choices'][0]['message']['content'].strip()

        # Output result
        print("Profile type:", profile_type)  # Should be either "person" or "group"
        return profile_type
    
    except Exception as e:
        print(f"Error during profile type classification: {e}")

def scrape_personal_data(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve the following contact details if available: email, phone number, Snapchat ID, Twitter ID, Tiktok ID and LinkedIn ID. If any of these are not found, return the value 'NA'.

        Your task is to return a JSON string in the following format and nothing else:
        {
        "email": "",
        "phone": "",
        "snapchat_id": "",
        "twitter_id": "",
        "tiktok_id":"",
        "linkedin_id": ""
        }
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response['choices'][0]['message']['content'].strip()

        # Try parsing to validate JSON
        try:
            contact_info = json.loads(result)
            print("Extracted Contact Info:")
            print(json.dumps(contact_info, indent=2))
        except json.JSONDecodeError:
            print("Response is not valid JSON. Raw output:")
            print(result)
    except Exception as e:
        print(f" Error during personal data scraping: {e}")

def profile_intelligence_engine():
    try:
        # Example data
        instagram_bio = "Fitness freak | NASM Certified | Helping you reach your goals 💪🇺🇸"
        influencer_location = "Los Angeles, USA"
        trimmed_instagram_caption = """
        Crushed leg day today! 💥💯
        Meal prep done for the week — gains incoming 🥗💪
        Quick home workout for busy bees 🐝🏋️‍♀️
        """
        instagram_url = "https://www.instagram.com/fitness_trainer_example/"
        business_category_name = "Fitness Trainer"
        trimmed_instagram_hashtags = "#fitness #gym #workout #fitspo #healthyliving"
        vertical_seggregation = classify_vertical(instagram_bio, influencer_location, trimmed_instagram_caption, trimmed_instagram_hashtags)
        profile_type = classify_profile_type(instagram_bio,business_category_name)
        personal_data = scrape_personal_data(instagram_bio,instagram_url)
        return vertical_seggregation
    
    except Exception as e:
        print(f"Error in AI agent orchestrator: {e}")