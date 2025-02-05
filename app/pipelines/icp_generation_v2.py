import os
import openai
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.utilities import ApifyWrapper
from langchain_core.document_loaders.base import Document
from langchain_openai import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings

# Set up your Apify API token and OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
apify = ApifyWrapper()

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
          Branding Manager,
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
          Business Development Managers,
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
          Abu dhabi,
          Sharjah,
          Ajman,
          Quatar,
          Oman,
          Saudi Arabia,
          Australia,
          France,
          South Africa,
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
          '1,500',
          '500,10000',
          '50,1000',
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
 
  client = openai.OpenAI(api_key=OPENAI_API_KEY)
  response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
  )
  # print(response.choices[0].message.content)
  result = response.choices[0].message.content
  return result


def create_icp(website_url):
    # website_url = "https://taippa.com/"
    
    # Run the Website Content Crawler on a website, wait for it to finish, and save its results into a LangChain document loader:
    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 20},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )

    print(loader.dataset_id) # Gives datasetid of the loader
    print("----Completed creating loader----")

    # Initialize the vector database with the text documents:
    index = VectorstoreIndexCreator(embedding=OpenAIEmbeddings()).from_loaders([loader])

    icp_justification_query = """
    Analyze the company's website and infer the Ideal Customer Profile (ICP) based on any available information.
    If complete details are not available, extract relevant insights from sections such as the About Us, Products/Services,
    Case Studies, Testimonials, and Blog content. Use indirect indicators like industry terms, client mentions, and service descriptions
    to form a reasoned ICP. Provide justification for your inference.
    """

    icp_justification = index.query_with_sources(icp_justification_query, llm=OpenAI(max_tokens=1000))

    print("Ideal Customer Profile Description:", icp_justification["answer"])
    print("source:", icp_justification["sources"])

    print("\n")

    icp_description_query = """
    Based on a detailed analysis of the company website, please help define the Ideal Customer Profile (ICP) for the company in the Dubai market. Specifically, provide the following:

    Job Titles: A list of relevant job titles of individuals who would benefit from company's services.
    Job Seniorities: A list of job seniorities (e.g., entry-level, mid-level, senior-level, etc.) that are most likely to be the decision-makers or key stakeholders.
    Person Locations: A list of potential locations where company's target customers are likely to be based.
    Company Size: The expected employee range of companies that would benefit from company's offerings.
    Please base your response on logical assumptions about the potential customers and their industries in the Dubai market, and align the profiles with company's services.
    """
    icp_result = index.query_with_sources(icp_description_query, llm=OpenAI(max_tokens=1000))

    print("Ideal Customer Profile Tags:", icp_result["answer"])
    print("source:", icp_result["sources"])

    icp_description = icp_result["answer"]
    apollo_tags = get_apollo_tags(icp_description)

    print(f"Apollo tags: {apollo_tags}")

    value_proposition_query = """
    Thoroughly analyze the available website content and extract key insights with **precise, relevant, and actionable details**.  
    Ensure that each section is structured into clear bullet points for better readability.  

    ### **Required Information:**  

    1. **Solution Benefits**  
      - Clearly identify the **core benefits** of the company's product/service.  
      - Highlight specific **value propositions**, such as cost savings, efficiency improvements, revenue growth, security enhancements, or regulatory compliance.  
      - Provide quantified benefits where possible (e.g., "Reduces operational costs by 30%" or "Increases lead conversion rates by 50%").  
      - If testimonials or customer success stories are available, extract relevant statements that reinforce these benefits.  

    2. **Unique Features**  
      - Identify distinct **functionalities, technologies, or methodologies** that set the product/service apart from competitors.  
      - Mention any **patented technology, proprietary algorithms, or exclusive integrations** that enhance the offering.  
      - Highlight industry-specific capabilities, automation features, AI-driven enhancements, or any **compliance-related advantages**.  

    3. **Solution Impact Examples**  
      - Provide **real-world examples, case studies, or use cases** demonstrating the impact of the product/service.  
      - Include relevant industries where the solution has been successfully implemented (e.g., "Used by leading fintech companies to streamline fraud detection").  
      - If no direct case studies are found, derive logical impacts based on the product's capabilities (e.g., "Given its AI-powered analytics, this tool likely helps e-commerce businesses optimize pricing strategies").  
      - **Avoid stating that information is unavailable**; instead, infer useful insights from context.  

    4. **Buyer Criteria**  
      - Clearly define the **target customers** based on their industry, business size, and geographic location.  
      - Specify the typical **pain points or challenges** these buyers face that the product/service addresses.  
      - Identify key decision-makers (e.g., CTOs, Marketing Directors, Procurement Managers) who would be involved in the purchasing process.  
      - Include details about **pricing expectations, regulatory considerations, and integration requirements** that may influence a buyer’s decision.  

    ### **Additional Instructions:**  
    - Ensure all extracted details are highly **specific, actionable, and relevant to the company’s product/service**.  
    - Do **not generalize**; instead, focus on precise insights derived from the website content.  
    - Present findings in **structured bullet points** to enhance clarity and ease of use.  
    """

    value_proposition_details = index.query_with_sources(value_proposition_query, llm=OpenAI(max_tokens=1000))

    print("Value Proposition Details:", value_proposition_details["answer"])
    print("source:", value_proposition_details["sources"])

if __name__ == "__main__":
  website_url = "https://www.tmeworldwide.com/"
  create_icp(website_url)
  


