import os
import requests

# from error_logger import execute_error_block

def generate_personalized_planner(industry,employee_count,technologies,description,country):

    # API endpoint and key
    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_API_KEY")  # Retrieve the API key from an environment variable

    if not api_key:
        return "Error: API key not found in environment variable PERPLEXITY_API_KEY"

    # Prompt for the Perplexity API
    prompt = f"""

    Provided the following information about an organization
    industry: {industry}
    employee_count: {employee_count}
    technologies: {technologies}
    description: {description}
    country: {country}

    Create a 15 day planner to boost the productivity and the sales of the organization relevant to the the details which has been provided here

    The main motive of the 15 day planner should be to serve as a excellent lead magnet providing a 15 day planner to improve their sales in the relevant market

    Refer all the relevant articles present in the internet which is available and create a excellent 15 day planner which is very efficient and precise

    Do not bold the headings, and ensure everything is presented as plain text.

    Output should be strictly text.
    """

    # Payload for the API request
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be concise and only output the requested metrics. Do not include sources."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300,
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "year",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    # Headers with API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        # Send the request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Extract and format the content
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "No content generated."
    except requests.exceptions.RequestException as e:
        return f"API request failed: {e}"

# Example usage
if __name__ == "__main__":
    industry = "information technology & services"  # Replace with the desired industry
    employee_count="2"
    technologies="['AI', 'Gmail', 'Google Apps', 'Google Cloud Hosting', 'Mobile Friendly', 'Remote', 'Varnish', 'Wix']"
    description="""
    CGNet was established as a representative of German Telecommunication & Payment Systems suppliers in Febr. 2006. It serves the MENA area encompassing the Middle East, North Africa, India, Pakistan and Sri Lanka regions.

    Information is a business's most important asset. CGNet provides the tools that can help you capitalize on it. By bringing our systems, software, services, and solutions together, we can work with you to put a comprehensive infrastructure to work for your business.
    """
    country= "Dubai, United Arab Emirates"
    content = generate_personalized_planner(industry,employee_count,technologies,description,country)
    print(content)