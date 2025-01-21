
# from error_logger import execute_error_block

import os
import requests
from client_info_parser import collect_information

def generate_personalized_planner(
        organization_name,
        organization_industry,
        organization_employee_count,
        organization_technologies,
        organization_description,
        organization_state,
        organization_country
        ):
    """
    Generates a 15-day planner to enhance productivity and sales for an organization using the Perplexity API.
    
    Args:
        industry (str): The organization's industry.
        employee_count (int): Number of employees in the organization.
        technologies (str): Technologies used by the organization.
        description (str): A brief description of the organization.
        country (str): The country where the organization operates.
    
    Returns:
        str: The generated 15-day planner or an error message.
    """

    # API endpoint and key
    url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "Error: API key not found in environment variable PERPLEXITY_API_KEY"

    updated_prompt = f"""
    Prompt: Create a 15-day sales improvement planner for {organization_name}

    Organization Details:
    - Name: {organization_name}
    - Industry: {organization_industry}
    - Employee Count: {organization_employee_count}
    - Technologies: {organization_technologies}
    - Description: {organization_description}
    - State: {organization_state}
    - Country: {organization_country}

    Objective:
    Develop a 15-day plan to enhance sales, productivity, and client attraction, tailored to {organization_name}'s specific needs and challenges in its industry, size, and market.

    Key Considerations:

    1. Industry Analysis:
    - Question: What are the current challenges and opportunities in {organization_industry} affecting sales?
    - Example: For Information Technology & Services, target client pain points like outdated systems, scalability issues, or security concerns.
    - Key Insight: Address these pain points in the plan, highlighting {organization_name}'s solutions.

    2. Geographical Context:
    - Question: How does {organization_name}'s location impact its market dynamics?
    - Example: In Dubai, focus on smart city development and tech infrastructure initiatives.
    - Key Insight: Align sales strategies with local initiatives and regional business needs.

    3. Technologies and Tools:
    - Question: How do {organization_name}'s technologies enhance its offering?
    - Example: Emphasize AI and cloud hosting as key selling points.
    - Key Insight: Showcase technical superiority in the plan, highlighting AI-driven insights and cloud-based services.

    4. Company Size and Resources:
    - Question: How does the team size influence the sales approach?
    - Example: Small team requires focused, hands-on approach to client relationships.
    - Key Insight: Prioritize targeted outreach and use automation tools to optimize resources.

    5. Sales Goals:
    - Question: What are realistic sales goals for {organization_name}?
    - Example: Generate 5-10 new leads per week.
    - Key Insight: Set achievable daily goals with measurable milestones.

    6. Lead Magnet Strategy:
    - Question: How to make this planner an effective lead magnet?
    - Example: Address specific challenges and provide solutions for the target market.
    - Key Insight: Include a CTA offering a consultation or demo of {organization_name}'s solutions.

    7. Actionable Steps:
    - Question: What daily tasks should be included in the 15-day plan?
    - Example: Progress from lead identification to closing deals.
    - Key Insight: Break down the plan into daily tasks:
        Days 1-3: Market Research and Lead Identification
        Days 4-7: Personalized Outreach
        Days 8-10: Content Marketing
        Days 11-15: Closing Deals and Retargeting

    Please create a detailed 15-day planner based on these considerations, tailored specifically to {organization_name}'s characteristics and needs.

    """

    prompt = f"""
        Prompt:
        We want to create a 15-day sales improvement planner tailored to {organization_name}, using the following details:

        Organization Details:
        Name: {organization_name}
        Industry: {organization_industry}
        Employee Count: {organization_employee_count}
        Technologies: {organization_technologies}
        Description: {organization_description}
        Organization State: {organization_state}
        Organization Country: {organization_country}

        Objective:
        Create a 15-day plan focused on improving sales, productivity, and client attraction while reflecting the specific needs and challenges faced by [Company Name] in its industry, size, and market.

        Key Considerations and Insights:
        Understanding the Organization's Industry:
        Question to Consider: What are the current challenges and opportunities in [Industry] that directly affect sales?
        Example Thought Process:
        Since [Industry] is [e.g., Information Technology & Services], potential customers are likely businesses looking for digital transformation and software solutions. We need to target client pain points such as outdated systems, scalability issues, or security concerns.
        Key Insight:
        Tailor the 15-day plan to address these pain points and highlight how [Company Name] provides solutions that directly respond to them.
        Target Market and Geographical Context:
        Question to Consider: How does [Company Name]’s location (e.g., Dubai, UAE) impact its market dynamics?
        Example Thought Process:
        In Dubai, there’s a strong push towards smart city development, tech infrastructure, and innovation. Clients in the region might be looking for cutting-edge solutions that align with government initiatives.
        Key Insight:
        Incorporate sales strategies that emphasize [Company Name]’s role in local initiatives, offering tailored solutions for businesses in the Middle East, North Africa, and South Asia.
        Technologies and Tools:
        Question to Consider: How do the technologies used by the company (e.g., AI, Google Cloud Hosting) enhance its offering?
        Example Thought Process:
        [Company Name] uses AI and cloud hosting, which are key selling points for businesses looking for scalable, secure, and innovative solutions.
        Key Insight:
        Showcase the technical superiority of [Company Name]’s solutions, highlighting AI-driven insights and cloud-based services to resonate with potential clients.
        Company Size and Resources:
        Question to Consider: How does the small team size (e.g., 2 employees) influence the sales approach?
        Example Thought Process:
        A smaller team might require a more focused, hands-on approach to building relationships with clients. It could also mean fewer resources for mass marketing, suggesting a more personalized outreach strategy.
        Key Insight:
        Prioritize targeted outreach to high-value prospects and use automation tools to streamline lead generation, optimizing time and resources.
        Setting Achievable Sales Goals:
        Question to Consider: What are realistic sales goals for a company with [Employee Count] employees and [Technology Stack]?
        Example Thought Process:
        With a small team, focusing on quality leads and long-term relationships is key. Setting an achievable goal, such as generating 5-10 new leads per week, is a good starting point.
        Key Insight:
        Set realistic goals for each day, ensuring measurable milestones and actionable tactics that lead to incremental growth.
        Lead Magnet Strategy:
        Question to Consider: How do we make this 15-day planner itself a lead magnet for potential clients?
        Example Thought Process:
        To make this planner an effective lead magnet, it must address specific challenges and provide solutions appealing directly to [Company Name]’s target market. The planner could serve as a free resource for potential clients, offering personalized advice on improving their own sales processes.
        Key Insight:
        At the end of the 15-day planner, include a call-to-action (CTA) offering a consultation or demo of [Company Name]’s solutions, highlighting how the company can further help clients improve their sales processes.
        Actionable Steps:
        Question to Consider: What daily tasks should be included to meet the goals outlined in the 15-day plan?
        Example Thought Process:
        Every day, the tasks should build on each other, starting with identifying high-potential leads, followed by personalized outreach, content creation (e.g., blog posts, case studies), and data-driven marketing efforts (using Google Cloud Analytics).
        Key Insight:
        Make the plan actionable by breaking it down into daily tasks:
        Day 1-3: Market Research and Lead Identification
        Day 4-7: Personalized Outreach
        Day 8-10: Content Marketing
        Day 11-15: Closing Deals and Retargeting
    """

    updated_prompt = f"""
    Objective: Create a 15-day sales improvement planner for {organization_name}

    Organization Profile:
    - Name: {organization_name}
    - Industry: {organization_industry}
    - Employees: {organization_employee_count}
    - Technologies: {organization_technologies}
    - Description: {organization_description}
    - Location: {organization_state}, {organization_country}

    Key Considerations:
    1. Industry Analysis
    2. Geographical Context
    3. Technologies and Tools
    4. Company Size and Resources
    5. Sales Goals
    6. Lead Magnet Strategy
    7. Actionable Steps

    Approach:
    Step 1: Analyze Current Situation
    - Evaluate organizational details
    - Assess context
    - Determine sales potential factors

    Step 2: Reasoning Process
    For each consideration:
    - Identify sales strategy implications
    - Connect insights to actionable steps

    Step 3: Detailed Reasoning
    - Explain decision-making process
    - Justify recommendations
    - Establish logical insight-action connections

    Deliverable:
    Provide a detailed 15-day planner tailored to {organization_name}'s characteristics and needs

    Include specific, achievable daily goals with measurable milestones.

    Output should just include 15 day planner nothing else, no additional content and plan should be specfic to separate days

    Example:
    Day 1: [Heading]
    - Action items

    Day 2: [Heading]
    - Action items

    .... Similarly for all

    Day 15: [Heading]
    - Action items

    """

    updated_prompt = f"""
    Objective:
    Create a 15-day sales improvement planner for {organization_name}, tailored to the organization's unique characteristics and needs.

    Organization Profile:
    - Name: {organization_name}
    - Industry: {organization_industry}
    - Employees: {organization_employee_count}
    - Technologies: {organization_technologies}
    - Description: {organization_description}
    - Location: {organization_state}, {organization_country}

    Key Considerations:
    1. Industry Analysis:
    - Evaluate current challenges and opportunities in {organization_industry} that impact sales.
    2. Geographical Context:
    - Assess how {organization_state}, {organization_country} influences market dynamics.
    3. Technologies and Tools:
    - Identify how {organization_technologies} enhance the organization’s sales offerings.
    4. Company Size and Resources:
    - Align strategies with the resources of an organization with {organization_employee_count} employees.
    5. Sales Goals:
    - Define realistic and measurable goals for the 15-day plan.
    6. Lead Magnet Strategy:
    - Create a plan that itself attracts potential clients.
    7. Actionable Steps:
    - Break the plan into clear, daily tasks with achievable milestones.

    Approach:
    Step 1: Analyze the Current Situation
    - Evaluate the organization's details and sales potential factors.

    Step 2: Apply Strategic Reasoning
    - For each key consideration, identify implications for sales strategies.
    - Develop actionable insights based on these considerations.

    Step 3: Create Detailed Recommendations
    - Justify the decision-making process for each step.
    - Ensure logical connections between insights and actions.

    Deliverable:
    - A detailed 15-day planner with specific daily goals and measurable milestones.
    - The output must include only the 15-day planner, with no additional content.

    Example Format:
    Day 1: [Heading]
    - Action items (For every action item, mention specifically relevant to {organization_industry} industry)

    Day 2: [Heading]
    - Action items (For every action item, mention specifically relevant to {organization_industry} industry)

    ...

    Day 15: [Heading]
    - Action items (For every action item, mention specifically relevant to {organization_industry} industry)
    """

    updated_prompt = f"""
    Objective:
    Create a 15-day sales improvement planner for {organization_name}, tailored to the organization's unique characteristics and needs.

    Organization Profile:
    - Name: {organization_name}
    - Industry: {organization_industry}
    - Employees: {organization_employee_count}
    - Technologies: {organization_technologies}
    - Description: {organization_description}
    - Location: {organization_state}, {organization_country}

    Key Considerations:
    1. **Industry Analysis**  
    - Evaluate current challenges and opportunities in {organization_industry} that impact sales.  

    2. **Geographical Context**  
    - Assess how {organization_state}, {organization_country}, influences market dynamics.  

    3. **Technologies and Tools**  
    - Identify how {organization_technologies} enhance the organization’s sales offerings.  

    4. **Company Size and Resources**  
    - Align strategies with the resources of an organization with {organization_employee_count} employees.  

    5. **Sales Goals**  
    - Define realistic and measurable goals for the 15-day plan.  

    6. **Lead Magnet Strategy**  
    - Create a plan that itself attracts potential clients.  

    7. **Actionable Steps**  
    - Break the plan into clear, daily tasks with achievable milestones.  

    Approach:
    1. **Analyze the Current Situation**  
    - Evaluate the organization's details and sales potential factors.  

    2. **Apply Strategic Reasoning**  
    - For each key consideration, identify implications for sales strategies.  
    - Develop actionable insights based on these considerations.  

    3. **Create Detailed Recommendations**  
    - Justify the decision-making process for each step.  
    - Ensure logical connections between insights and actions.  

    Deliverable:
    - A detailed 15-day planner with specific daily goals and measurable milestones.  
    - The output must include only the 15-day planner, with no additional content.  

    Example Format:
    Day 1: [Heading]  
    - Action items (For every action item, mention specific relevance to {organization_industry} industry.)  

    Day 2: [Heading]  
    - Action items (For every action item, mention specific relevance to {organization_industry} industry.)  

    ...  

    Day 15: [Heading]  
    - Action items (For every action item, mention specific relevance to {organization_industry} industry.)  
    """

    # API request payload
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "Be concise and only output the requested metrics. Do not include sources."},
            {"role": "user", "content": updated_prompt}
        ],
        "max_tokens": 2000,
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

    # Send API request
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Parse response
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
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

    # details = collect_information("nadia@cgnet.ae")
    # details = collect_information("sravan.workemail@gmail.com")
    details = collect_information("timofey.borzov@vtbcapital.com")
    # timofey.borzov@vtbcapital.com

    organization_name = details.get('organization_name')
    organization_industry = details.get('organization_industry')
    organization_employee_count = details.get('organization_employee_count')
    organization_technologies = details.get('organization_technologies')
    organization_description = details.get('organization_description')
    organization_state = details.get('organization_state')
    organization_country = details.get('organization_country')

    content = generate_personalized_planner(
        organization_name=organization_name,
        organization_industry=organization_industry,
        organization_employee_count=organization_employee_count,
        organization_technologies=organization_technologies,
        organization_description=organization_description,
        organization_state=organization_state,
        organization_country=organization_country
        )
    print(content)