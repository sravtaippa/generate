import openai
import json
import os
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchResults
import json
import requests
from db.db_utils import unique_key_check_airtable,export_to_airtable

from config import APOLLO_HEADERS

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLIENT_CONFIG_TABLE_NAME = os.getenv("CLIENT_CONFIG_TABLE_NAME")

# Initialize the OpenAI model
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

# LangChain Prompt Templates for ICP generation and website analysis
icp_template = """
Create an Ideal Customer Profile (ICP) for the following company based on its description:

Company Description:
{input}

The ICP should include:
1. person_titles[]
2. person_locations[]
3. person_seniorities[]
4. organization_locations[]
5. organization_size[]
"""
icp_prompt = PromptTemplate(input_variables=["input"], template=icp_template)

company_info_template = """
Analyze the following website and provide concise information about the company:
- Description of the company
- The sector they belong to
- What they are selling or offering

Website URL: {input}
"""
company_info_prompt = PromptTemplate(input_variables=["input"], template=company_info_template)

# Initialize LLMChains for ICP generation and section segregation
icp_chain = LLMChain(prompt=icp_prompt, llm=llm)
company_info_chain = LLMChain(prompt=company_info_prompt, llm=llm)

search_tool = DuckDuckGoSearchResults()

def fetch_website_content(website_url):
    """
    Fetches website content using DuckDuckGo search results.
    """
    try:
        search_result = search_tool.run(website_url)
        return {"website_url": website_url, "website_content": search_result}
    except Exception as e:
        return {"error": f"Error fetching website content: {e}"}

def process_workflow(website_url):
    """
    Main workflow to process website content, generate ICP, and segregate sections.
    """
    # Step 1: Fetch website content
    print("\n--- Fetching Website Content ---")
    website_content = fetch_website_content(website_url)

    if "error" in website_content:
        print(f"Error: {website_content['error']}")
        return

    website_description = website_content.get("website_content", "")
    print(f"Website Content: {website_description}\n")

    # Step 2: Generate ICP
    print("--- Generating Ideal Customer Profile (ICP) ---")
    try:
        icp_result = icp_chain.run(input=website_description)
        print(f"ICP Result: {icp_result}\n")
    except Exception as e:
        print(f"Error generating ICP: {e}")
        return

    # Output results
    print("=== Final Results ===")
    print("Website Content:", website_description)
    print("Ideal Customer Profile:", icp_result)
    return icp_result

def get_apollo_tags(icp_information):
    prompt = f"""
    From the information gathered regarding the Ideal Customer Profile of the company: {icp_information}, segregate the details into different sections:
    1. job_titles
    2. person_seniorities
    3. person_locations
    4. employee_range

    Pick job_titles from the following options which are relevant to the given Ideal Customer Profile:
    job_titles = [
        CEO,
        COO,
        CTO,
        CMO,
        CIO,
        CFO,
        VP of Sales,
        VP of Marketing,
        VP of Engineering,
        Director of Sales,
        Director of Marketing,
        Director of Product Management,
        Director of Operations,
        Director of HR,
        Director of Engineering,
        Sales Manager,
        Marketing Manager,
        Product Manager,
        Operations Manager,
        HR Manager,
        IT Manager,
        Customer Success Manager,
        Software Engineer,
        Data Scientist,
        Product Designer,
        Marketing Specialist,
        Sales Representative,
        Business Analyst,
        UX Designer,
        Customer Support Specialist,
        Junior Software Engineer,
        Marketing Assistant,
        Sales Associate,
        HR Coordinator,
        Administrative Assistant,
        Founder,
        Co-Founder,
        Partner,
        Consultant,
        Freelancer,
        Contractor,
        Intern,
        Growth Hacker,
        Scrum Master,
        DevOps Engineer,
        Machine Learning Engineer,
        Social Media Strategist,
        Content Creator
    ]

    Pick person_seniorities that fall under these categories which are relevant to the given Ideal Customer Profile::
    person_seniorities = [
        Founder,
        Training,
        Entry,
        Senior,
        Manager,
        Director,
        VP,
        Founder,
        C-Level,
        Partner,
        Owner,
        Board Member
    ]

    Pick person_locations that fall under these categories which are relevant to the given Ideal Customer Profile understanding the sector (select minimum 1 atleast):
    person_locations = [
        Dubai,
        United Arab Emirates,
        India,
        China,
        United States,
        Russia,
        Germany,
        Italy,
        Canada,
        United Kingdom,
    ]

    Pick employee range based on the estimate number of organization employee based on the relevance of the industry of Ideal Customer Profile proved
    employee_range = [
      '1,20',
      '1,50',
      '1,100',
      '100,10000'
    ]

    Output should ONLY be a JSON object with the following structure:
    {{
      "job_titles": [job_title1, job_title2, job_title3],
      "person_seniorities": [person_seniority1, person_seniority2, person_seniority3],
      "person_locations": [person_location1,person_location2,person_location3],
      "employee_range": [employee_range1,employee_range2,employee_range3]
    }}

    Do not include any explanations, text, or additional information outside the JSON object.
    """

    prompt = f"""
    From the information gathered regarding the Ideal Customer Profile of the company: {icp_information}, segregate the details into different sections:
    1. job_titles
    2. person_seniorities
    3. person_locations
    4. employee_range

    Pick job_titles from the following options which are relevant to the given Ideal Customer Profile:
    job_titles = [
        CEO,
        COO,
        CTO,
        CMO,
        CIO,
        CFO,
        VP of Sales,
        VP of Marketing,
        VP of Engineering,
        Director of Sales,
        Director of Marketing,
        Director of Product Management,
        Director of Operations,
        Director of HR,
        Director of Engineering,
        Sales Manager,
        Marketing Manager,
        Product Manager,
        Operations Manager,
        HR Manager,
        IT Manager,
        Customer Success Manager,
        Software Engineer,
        Data Scientist,
        Product Designer,
        Marketing Specialist,
        Sales Representative,
        Business Analyst,
        UX Designer,
        Customer Support Specialist,
        Junior Software Engineer,
        Marketing Assistant,
        Sales Associate,
        HR Coordinator,
        Administrative Assistant,
        Founder,
        Co-Founder,
        Partner,
        Consultant,
        Freelancer,
        Contractor,
        Intern,
        Growth Hacker,
        Scrum Master,
        DevOps Engineer,
        Machine Learning Engineer,
        Social Media Strategist,
        Content Creator
    ]

    Pick person_seniorities that fall under these categories which are relevant to the given Ideal Customer Profile:
    person_seniorities = [
        owner,
        founder,
        c_suite,
        partner,
        vp,
        head,
        director,
        manager,
        senior,
        entry,
        intern,
    ]

    Pick person_locations that fall under these categories which are relevant to the given Ideal Customer Profile, understanding the sector (select minimum 1 at least):
    person_locations = [
        Dubai,
        United Arab Emirates,
        India,
        China,
        United States,
        Russia,
        Germany,
        Italy,
        Canada,
        United Kingdom
    ]

    Pick employee range based on the estimated number of organization employees, based on the relevance of the industry of Ideal Customer Profile:
    employee_range = [
        '1,100',
        '1,1000',
        '1,50'
    ]

    Output should ONLY be a JSON object with the following structure:
    {{
      "job_titles": [job_title1, job_title2, job_title3],
      "person_seniorities": [person_seniority1, person_seniority2, person_seniority3],
      "person_locations": [person_location1, person_location2, person_location3],
      "employee_range": [employee_range1, employee_range2, employee_range3]
    }}

    Do not include any explanations, text, or additional information outside the JSON object.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a JSON text formatter. Only output the exact JSON text requested, with no additional text, explanations, or formatting."
            },
            {"role": "user", "content": prompt}
        ]
    )
    result = response['choices'][0]['message']['content']
    # print(type(result))
    return result

def construct_query_param_range(key, values):
    print("&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values]))
    return "&".join([f"{key}[]={value.replace(',', '%2C')}" for value in values])

def construct_query_param_keywords(key, value):
    return f"{key}={value.replace(',', '%2C').replace(' ','%20')}"

def construct_query_param(key, values):
    res = "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])
    print(res)
    return "&".join([f"{key}[]={value.replace(' ', '%20').replace(',', '%2C')}" for value in values])

def generate_icp(client_id,website_url):
    try:
        print(f"\n\n--------Generating ICP--------\n\n")
        openai.api_key = OPENAI_API_KEY
        icp_result = process_workflow(website_url)
        icp_tags = get_apollo_tags(icp_result)
        icp_json = json.loads(icp_tags)
        results_per_page=100
        person_titles = icp_json.get('job_titles')
        person_seniorities = icp_json.get('person_seniorities')
        person_locations = icp_json.get('person_locations')
        email_status = ['verified']
        organization_num_employees_ranges = icp_json.get('employee_range')
        print(f"\n\n--------Creating query params--------\n\n")
        query_params = [
                    construct_query_param("person_titles", person_titles),
                    construct_query_param("person_seniorities", person_seniorities),
                    construct_query_param("person_locations", person_locations),
                    construct_query_param("organization_locations", person_locations),
                    construct_query_param("contact_email_status", email_status),
                    construct_query_param_range("organization_num_employees_ranges", organization_num_employees_ranges),
        ]
        query_params_test = query_params.copy()
        query_params_test.append("page=1")
        query_params.append("page={page_number}")
        query_params.append("per_page={records_required}")
        query_params_test.append(f"per_page={results_per_page}")
        base_url = "https://api.apollo.io/api/v1/mixed_people/search"
        url_test = f"{base_url}?{'&'.join(query_params_test)}"
        dynamic_url = f"{base_url}?{'&'.join(query_params)}"
        headers = APOLLO_HEADERS
        print(f"\n\nRunning the people search API test")
        response = requests.post(url_test, headers=headers)
        if response.status_code == 200:
            print(f"\n------------Completed Persona Data Mining------------")
            data = response.json()
            print(f"No of profiles collected : {len(data['people'])}")
            record_exists = unique_key_check_airtable('client_id',client_id,CLIENT_CONFIG_TABLE_NAME)
            if record_exists:
                print(f'Record with the following id: {client_id} already exists for client config table. Skipping the entry...')
                return True
            config_data = {
                "client_id":client_id,
                "icp_url":dynamic_url,
                "icp_description":icp_result,
                "icp_job_details":str(person_titles),
                "icp_job_seniorities":str(person_seniorities),
                "icp_employee_range":str(organization_num_employees_ranges),
                "icp_locations":str(person_locations),
                "page_number":'1',
                "qualify_leads":'no',
                "records_required":'5'
            }
            export_to_airtable(config_data, CLIENT_CONFIG_TABLE_NAME)
        return dynamic_url
    
    except Exception as e:
        print(f"Error occured at {__name__} while generating icp: {e}")
        return False

if __name__=="__main__":
    pass