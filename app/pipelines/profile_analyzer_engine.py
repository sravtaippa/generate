import openai
import json
import os

from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

openai.api_key =  OPENAI_API_KEY 


def classify_vertical(instagram_bio, influencer_location, trimmed_instagram_caption, trimmed_instagram_hashtags):
    try:

        # Define system + user messages
        system_prompt = """
        You are a an advanced AI assistant programmed to analyze social media profiles of users. Based on the provided information, classify the user into the following categories and return a valid JSON string as output.

        - The "targeted_domain" can have multiple values from these options (need not be limited to one value): ["food", "fashion", "fitness", "gaming", "education", "automotive", "finance", "art"]. Eg: food,lifestyle.
        - The "targeted_audience" must be ONLY one of: ["gen-z", "gen-y", "gen-x"] & cannot contain multiple values, based on user's content and who the targeted audience can be. Use this information to determine the closest targeted audience:
           1. gen-z: born between 1997–2012 (mostly teens and young adults)
           2. gen-y: born between 1981–1996 (millennials, young professionals)
           3. gen-x: born between 1965–1980 (older adults, parents)

        - The "influencer_nationality" should be inferred from the bio and current location if possible. If not clear, set to "unknown".

        Your output must be a valid JSON object **without** any markdown formatting, explanation, or additional commentary. Do **not** include code blocks, quotes, or descriptive text. Just the JSON string object in this format:
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

        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        result = response.choices[0].message.content

        # Validate it's a JSON string (not markdown-formatted)
        try:
            parsed = json.loads(result)
            print("Classification Result:")
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError:
            print("The response is not a valid JSON string. Here's the raw output:")
            print(result)
        return result
    except Exception as e:
        print(f" Error during classification: {e}")


def classify_profile_type(instagram_bio,business_category_name):
    try:
        # Define the system and user prompts
        system_prompt = """
        You are a smart assistant programmed to analyze social media profiles and determine whether the profile belongs to an individual or a group/team.

        Possible profile types:
        - person (belonging to an individual)
        - group (belonging to a team, organization, or business (eg: restaurants,brands, etc))

        Your task is to return only one of the above tags, and nothing else.
        """

        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, business_category_name: {business_category_name}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        profile_type = response.choices[0].message.content

        # Output result
        print("Profile type:", profile_type)  # Should be either "person" or "group"
        
    except Exception as e:
        print(f"Error during profile type classification: {e}")

    return profile_type

def get_phone(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve phone number if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the phone number or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )
        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result

def get_email(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve email ID if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the email ID or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result

def get_snapchat_id(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve Snapchat ID if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the Snapchat ID or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result


def get_linkedin_id(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve LinkedIn ID if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the LinkedIn ID or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result

def get_twitter_id(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve twitter ID if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the twitter ID or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result

def get_tiktok_id(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve tiktok ID if available. If not found, return the value 'NA'.
        Output should be a plain text containing only the tiktok ID or 'NA' if not found. Do not include any other text or markdown formatting or explanations.
        """

        # Define the user prompt
        user_prompt = f"""
        Provided info about the profile:
        bio: {instagram_bio}, instagram_url: {instagram_url}
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content
        
    except Exception as e:
        print(f" Error during personal data scraping: {e}")
    return result


def scrape_personal_data(instagram_bio,instagram_url):
    try:
        # Define the system prompt
        system_prompt = """
        You are a smart assistant programmed to scrape social media bio and retrieve the following contact details if available: email, phone number, Snapchat ID, Twitter ID, Tiktok ID and LinkedIn ID. If any of these are not found, return the empty string value ''.

        Your task is to return a JSON string in the following format and nothing else, don't add any other text or markdown formatting:
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

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            temperature=0.0
        )

        # Extract and print result
        result = response.choices[0].message.content

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

    return result

def profile_intelligence_engine(instagram_bio, influencer_location, trimmed_instagram_caption, instagram_url, business_category_name, trimmed_instagram_hashtags):
    try:
        vertical_seggregation = classify_vertical(instagram_bio, influencer_location, trimmed_instagram_caption, trimmed_instagram_hashtags)
        profile_type = classify_profile_type(instagram_bio,business_category_name)
        personal_data = scrape_personal_data(instagram_bio,instagram_url)
        print(f"Vertical Segregation: {vertical_seggregation}")
        print(f"Profile Type: {profile_type}")
        print(f"Personal Data: {personal_data}")
        vs_dict = json.loads(vertical_seggregation)
        pd_dict = json.loads(personal_data)
        influencer_data = vs_dict | pd_dict | {"profile_type": profile_type}
        print(f"Final Influencer Data: {influencer_data}")
        return influencer_data
    
    except Exception as e:
        print(f"Error in AI agent orchestrator: {e}")