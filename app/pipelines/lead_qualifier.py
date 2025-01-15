import openai
from error_logger import execute_error_block
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,AIRTABLE_TABLE_NAME,APOLLO_API_KEY,APOLLO_HEADERS

def qualify_lead(persona_details,solution_benefits,unique_features,solution_impact_examples,domain,buyer_criteria,buyer_examples):
    try:
        title = persona_details['title']
        headline = persona_details['headline']
        country = persona_details['country']
        city = persona_details['city']
        departments = persona_details['departments']
        subdepartments = persona_details['subdepartments']
        functions = persona_details['functions']
        employment_summary = persona_details['employment_summary']

        lead_prompt = f"""
        Given the following details about a person:
        - Title: {title}
        - Headline: {headline}
        - Country: {country}
        - City: {city}
        - Departments: {departments}
        - Subdepartments: {subdepartments}
        - Functions: {functions}
        - Employment Summary: {employment_summary}

        Here is information about our company and the product we offer:
        - Solution benefits: {solution_benefits}
        - Unique features: {unique_features}
        - Solution impact: {solution_impact_examples}
        - Domain: {domain}
        - Targeted buyer criteria: {buyer_criteria}

        Below are examples of warm lead profiles. These are generic examples, which means this is not exactly how they should look:
        {buyer_examples}

        If no examples are provided, you can use the already existing information

        Now, based on the provided details, does this person match the profile of a 'warm' lead for our company?
        Answer with **Yes/No** and provide a brief justification.
        """

        # Send the request to OpenAI GPT-4
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": lead_prompt}
            ]
        )
        # Print the response
        qualification_response = response['choices'][0]['message']['content']
        print('===============================================\n')
        print(f"Qualification status : {qualification_response}")
        print('===============================================\n')
        qualification_status=qualification_response[:5]
        return True if 'YES' in qualification_status.upper() else False
    except Exception as e:
        execute_error_block(f"Error occured in {__name__} while qualifying the lead. {e}")

def qualify_lead_test(persona_details, solution_benefits, unique_features, 
                      solution_impact_examples, domain, buyer_criteria, buyer_examples):
    try:
        title = persona_details['title']
        headline = persona_details['headline']
        country = persona_details['country']
        city = persona_details['city']
        departments = persona_details['departments']
        subdepartments = persona_details['subdepartments']
        functions = persona_details['functions']
        employment_summary = persona_details['employment_summary']
        
        lead_prompt = f"""
            Step 1:
            Please provide the average salary of a {title} in {city} with {city} currency per month. 
            Just provide the salary amount, without any justification or additional information. 
            The output should look like this: 18000

            Step 2:
            Please format the output from Step 1 as: 
            "Salary is (output from Step 1)"
            Only output this formatted statement, nothing else.
        """
        print(lead_prompt)
        # lead_prompt = """
        #     Please provide the average salary of a Data Engineer in Dubai with Dubai currency per month, 
        #     Just provide the average salary dont give justification
        #     output should look like this: average_salary: 18000 AED per month. 
        # """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": lead_prompt}
            ]
        )
        # Print the response
        qualification_response = response['choices'][0]['message']['content']
        print('===============================================\n')
        print(f"HNWI Qualification status : {qualification_response}")
        print('===============================================\n')
        return True
    
    except Exception as e:
        execute_error_block(f"Error occurred in {__name__} while running the test qualification for the lead. {e}")