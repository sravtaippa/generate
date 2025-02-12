import os
import openai
from langchain.indexes import VectorstoreIndexCreator
from langchain_community.utilities import ApifyWrapper
from langchain_core.document_loaders.base import Document
from langchain_openai import OpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain.indexes.vectorstore import VectorstoreIndexCreator
# from langchain.llms import OpenAI
from transformers import GPT2TokenizerFast  # For token counting
from langchain_community.vectorstores import Chroma
from error_logger import execute_error_block
from datetime import datetime, timezone
# import datetime

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Set up your Apify API token and OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
apify = ApifyWrapper()

def get_client_value_proposition(tokenizer,index):
  try:
    print(f"----------Started Client Value Proposition Analysis ----------")
    value_proposition_query_v2 = """
    Provide a detailed overview of the company based on the extracted content. 
    Include the following aspects explicitly if mentioned: 
    - The company's full name and industry.  
    - A brief company history and major milestones.  
    - Core offerings, products, or services.  
    - Target audience or industries served.  
    - Unique value propositions or differentiating factors.  
    - Major clients, partnerships, and collaborations.  
    - Key financials (if available), such as revenue, market position, or growth metrics.  
    - Any other notable details that define the company's market presence.  
    Ensure the response is **strictly based on extracted content** without assumptions.
    """

    # Increase retrieval depth and improve relevance
    retriever = index.vectorstore.as_retriever(search_kwargs={"k": 30})  # Increased `k`
    retrieved_docs = retriever.invoke(value_proposition_query_v2)

    # Filter out empty or irrelevant documents
    filtered_docs = [doc for doc in retrieved_docs if len(doc.page_content.strip()) > 50]  # Adjust threshold as needed

    # Extract text from the top-ranked relevant documents
    retrieved_texts = [doc.page_content for doc in filtered_docs]
    sources = [doc.metadata.get("source", "Unknown") for doc in filtered_docs]

    # Print Retrieved Document Count
    print(f"Retrieved {len(filtered_docs)} relevant documents.")

    context = "\n\n".join(retrieved_texts)
    tokenized_context = tokenizer.encode(context, truncation=True, max_length=2200)
    trimmed_context = tokenizer.decode(tokenized_context)

    client_value_proposition_prompt = f"""
    ### 🚀 Extract Verified Company Information – No Assumptions 🚀  
    You are analyzing structured company information strictly based on **verified website content**.  
    Your task is to **extract and categorize details** under the specified sections.  

    🚨 **Rules:**  
    ✅ Use **only** the information provided in the context.  
    🚫 **Do NOT infer or assume** missing details.  
    🚫 **Do NOT include generic industry knowledge.**  

    ---  
    ### **Company Overview**  
    🔹 **Company Name & Industry:** Identify the company's official name and industry.  
    🔹 **Company History & Milestones:** List achievements, partnerships, or significant events (only if explicitly mentioned).  

    ### **Unique Company Aspects**  
    🔹 **Key Offerings:** Provide a detailed list of **products, solutions, or services** mentioned. Avoid generic descriptions.  
    🔹 **Target Audience:**  
      - Identify **specific industries** the company serves (e.g., Healthcare, Finance, Retail, Manufacturing, etc.).  
      - List any **specific client names or sectors** if mentioned.  
      - If industry names are **not explicitly mentioned**, list **examples of products/services** that indicate industry focus.  
    🔹 **Differentiating Factors:** Highlight what makes the company unique (e.g., proprietary tech, partnerships).  

    ### **Competitive Positioning & Market Impact**  
    🔹 **Major Clients & Partnerships:** List major clients, collaborations, or industry partnerships (if stated).  
    🔹 **Key Statistics:** Extract **quantitative data** such as revenue, growth metrics, or market share (if available).  

    ---  
    📌 **Extracted Website Content:**  
    {trimmed_context}  

    📌 **Structured Response:**  
    """

    llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space
    client_value_proposition = llm.invoke(client_value_proposition_prompt)
    
    print("\nClient Value Proposition:", client_value_proposition)
    print("\nSources:", sources)
    return client_value_proposition

  except Exception as e:
    execute_error_block(f"Error occured while getting client value proposition, {e}")

def get_icp(tokenizer,index):
  try:
      print("================ Analyzing Ideal Customer Profile ======================\n\n")
      content_extraction_query = """
      Retrieve and extract all available information to determine the Ideal Customer Profile (ICP) of the company. 
      Focus only on explicitly mentioned data and avoid assumptions.

      ### **What to Extract?**  
      1️⃣ **Industries & Business Types Served:** Look for direct mentions of industry names, business categories, or sectors.  
      2️⃣ **Customer Segments:** Identify key client groups (e.g., startups, enterprises, government, e-commerce).  
      3️⃣ **Geographical Focus:** Extract locations where the company operates or provides services.  
      4️⃣ **Case Studies & Testimonials:** Identify customer success stories, mentions of previous clients, or reference businesses.  
      5️⃣ **Pain Points Solved:** Identify challenges the company addresses for its clients (if explicitly stated).  

      📌 **Extraction Scope:** Use content from the "About Us," "Products/Services," "Case Studies," "Testimonials," and blog sections if available.  
      📌 **Strictly No Assumptions:** Only use details explicitly mentioned in the dataset.  

      Return all extracted information in a structured format.  
      """

      # Increase retrieval depth and improve relevance
      retriever = index.vectorstore.as_retriever(search_kwargs={"k": 30})  # Increased `k`
      retrieved_docs = retriever.invoke(content_extraction_query)

      # Filter out empty or irrelevant documents
      filtered_docs = [doc for doc in retrieved_docs if len(doc.page_content.strip()) > 50]  # Adjust threshold as needed

      # Extract text from the top-ranked relevant documents
      retrieved_texts = [doc.page_content for doc in filtered_docs]
      sources = [doc.metadata.get("source", "Unknown") for doc in filtered_docs]

      # Print Retrieved Document Count
      print(f"Retrieved {len(filtered_docs)} relevant documents.")

      # Join retrieved content
      context = "\n\n".join(retrieved_texts)

      # Truncate the input dynamically
      tokenized_context = tokenizer.encode(context, truncation=True, max_length=1500)
      trimmed_context = tokenizer.decode(tokenized_context)
      # print(trimmed_context)

      explicit_icp_criteria = "Not available"
      prompt_expanded = f"""
      ### Task: Extract Ideal Customer Profile (ICP) from Website Content

          #### **🔍 Objective**
          Analyze the **company's website** to extract its **Ideal Customer Profile (ICP)** based on **industry, market positioning, and offerings**.  
          The ICP will help retrieve **high-value prospects** from **Apollo.io** for **targeted outreach**.  

          ---

          #### **🚨 STRICT Criteria**  
          ✔ **Primary Source:** Extract ICP attributes **strictly from website content**.  
          ✔ **Explicit Criteria:** If provided (`{explicit_icp_criteria}`), prioritize it **alongside** website insights.  
          ✔ **If `{explicit_icp_criteria}` = `"Not available"`, rely entirely on website content**.  
          ✔ **STRICTLY exclude irrelevant profiles.**  

          ---

          #### **📌 ICP Attributes to Extract**  

          ##### **1️⃣ Job Titles (Minimum 5 - STRICT, No Invalid Responses)**  
          🔴 **IMPORTANT**:  
          - **ALWAYS return at least 5 job titles**.  
          - If fewer than 5 job titles exist, **infer closely related job titles** from context instead of returning fewer than 5.  
          - If no exact matches are available, **derive general industry-relevant job titles**.  

          ##### **2️⃣ Seniority Levels (Minimum 4 - STRICT, Unique Values Required)**  
          🔴 **IMPORTANT**:  
          - Extract at least **4 unique seniority levels**.  
          - **DO NOT repeat the same seniority level** (e.g., avoid `["Senior", "Senior", "Senior", "Senior"]`).  
          - If limited seniority data is available, **infer additional relevant seniority levels**.  

          ##### **3️⃣ Geographic Targeting (At Least 1, Can Be More - Unique Countries Required)**  
          🔴 **IMPORTANT**:  
          - Extract **at least 1 country**, but **include multiple if available**.  
          - Ensure extracted locations are **strictly countries** (e.g., avoid cities or regions like `"Dubai"`, use `"United Arab Emirates"`).  
          - If the company’s client locations are not explicitly mentioned, **extract the company's location and include nearby countries**.  

          ##### **4️⃣ Ideal Company Size - Minimum 3 Ranges (STRICT)**  
          - **Extract at least 3 distinct company size tags** (e.g., `'1-10'`, `'11-50'`, `'51-200'`).  

          ---

          #### **✅ Extraction Guidelines**  
          ✔ **Website content is the primary source.**  
          ✔ If `{explicit_icp_criteria}` is available, **merge it with extracted insights**.  
          ✔ STRICTLY **ensure minimum counts for each category.**  
          ✔ **NEVER return "INVALID" or an empty list—always generate the closest possible matches**.  
          ✔ **Ensure diversity in extracted values (no duplicates within lists).**  

          ---

          #### **🚀 JSON-ONLY Output**  
          ⚠️ **Return ONLY a JSON object** with unique values in each category—DO NOT include explanations.  

          ```json
          {{
            "job_titles": ["<job_title_1>", "<job_title_2>", "<job_title_3>", "<job_title_4>", "<job_title_5>", ...],
            "person_seniorities": ["<unique_seniority_1>", "<unique_seniority_2>", "<unique_seniority_3>", "<unique_seniority_4>", ...],
            "person_locations": ["<unique_location_1>", "<unique_location_2>", "<unique_location_3>", ...],
            "employee_range": ["<size_1>", "<size_2>", "<size_3>", ...]
          }}
      ---  
      📌 **Extracted Website Content:**  
      {trimmed_context}  

      📌 **Structured Response:**  
      """
      
      llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space

      icp_tags = llm.invoke(prompt_expanded)
      print("\n🚀 ICP tags:\n", icp_tags)
      print("\n📌 Sources:", sources)

      icp_analysis_prompt = f"""
          Analyze the **company's website content** to extract its **Ideal Customer Profile (ICP)** based on **industry, market positioning, and offerings**.  
          The ICP will help retrieve **high-value prospects** from **Apollo.io** for **targeted outreach**.  
          company's website content: {trimmed_context}
      """
      llm = OpenAI(temperature=0, max_tokens=1500)  # Increased output space

      icp_analysis = llm.invoke(icp_analysis_prompt)
      print("\n🚀 ICP analysis:\n", icp_analysis)
      print("\n📌 Sources:", sources)
      return icp_tags,icp_analysis

  except Exception as e:
    execute_error_block(f"Error occured while fetching the ICP. {e}")

def get_apollo_tags(icp_information):
  try:
    prompt = f"""
        From the information gathered regarding the Ideal Customer Profile of the company: {icp_information}, segregate the details into different sections:
        1. job_titles
        2. person_seniorities
        3. person_locations
        4. employee_range

        Pick job_titles from the following options which are relevant to the given Ideal Customer Profile (select minimum 5 at least):
        job_titles = [
            CEO,
            COO,
            CTO,
            CMO,
            CIO,
            CFO,
            E-commerce Specialist,
            VP of Sales,
            Marketing Manager,
            Marketing Coordinator,
            Digital Marketing Manager,
            Director of Marketing,
            Director of Sales,
            Business Development Managers,
            Sales Associate,
            VP of Marketing,
            VP of Engineering,
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
            Data Scientist,
            Product Designer,
            Marketing Specialist,
            Sales Representative,
            Business Analyst,
            Customer Support Specialist,
            Marketing Assistant,
            Sales Associate,
            HR Coordinator,
            Business Development Managers,
            Administrative Assistant,
            Freelancer,
            Contractor,
            Growth Hacker,
            Scrum Master,
            Social Media Strategist,
            Content Creator
        ]

        Pick person_seniorities that fall under these categories which are relevant to the given Ideal Customer Profile :
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

        Pick person_locations that fall under these categories which are relevant to the given Ideal Customer Profile (minimum 1 required):
        person_locations = [
            Dubai,
            UAE,
            United Arab Emirates,
            Abu dhabi,
            Sharjah,
            Ajman,
            Riyadh,
            Manama,
            Bahrain,
            Muscat,
            Kuwait,
            Jordan,
            Lebanon,
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
            '1,50',
            '11,50',
            '51,200',
            '201,500',
            '501,1000',
            '1000,5000',
            '5001,10000',
        ]

        Return only a **STRICT** JSON object in the following format:
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
  except Exception as e:
   execute_error_block(f"Error occured while creating apollo tags: {e}") 

def analyze_website(website_url,explicit_icp_criteria="Not available"):
  try:
    print(" Started Website Analysis")
    print("\n--------------------------------------------------------\n")
    print("Initiating the Apify Actor run...")
    loader = apify.call_actor(
        actor_id="apify/website-content-crawler",
        run_input={"startUrls": [{"url": website_url}], "maxCrawlPages": 20},
        dataset_mapping_function=lambda item: Document(
            page_content=item["text"] or "", metadata={"source": item["url"]}
        ),
    )

    time_stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M-%S')
    print(f"Time : {time_stamp}")
    chroma_folder = f"chroma_data_{website_url.replace('https://', '').replace('/', '_')}_{time_stamp}"
    print(f"Chroma folder name: {chroma_folder}")
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    print(f"Dataset id of the loader : {loader.dataset_id}") # Gives datasetid of the loader
    
    # Step 1: Define Embeddings & Vector Store Index
    embedding_function = OpenAIEmbeddings()

    print(f"Fetching vector store index")
    # Now use sqlite3 as usual
    import sqlite3
    print(f"Sqlite3 version : {sqlite3.sqlite_version}")  
    index = VectorstoreIndexCreator(
        vectorstore_cls=Chroma,  
        embedding=embedding_function,  
        vectorstore_kwargs={"persist_directory": chroma_folder}  
    ).from_loaders([loader])  
    print(f"Started website analysis...")
    icp_tags,icp_analysis = get_icp(tokenizer,index)
    apollo_tags = get_apollo_tags(icp_tags)
    client_value_proposition = get_client_value_proposition(tokenizer,index)
    print(f"Apollo tags: {apollo_tags}")

    print("================Completed Web analysis======================\n\n")
    

    print("\n--------------------------------------------------------\n")
    icp_details = icp_analysis + "\n\n" + icp_tags
    return icp_details,apollo_tags,client_value_proposition
  
  except Exception as e:
    print(f"Error occured while analyzing the website : {e}")


def chroma_db_testing():
    try:
        # Replace sqlite3 with pysqlite3
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

        # Now use sqlite3 as usual
        import sqlite3
        print(sqlite3.sqlite_version)  

        return True
    except Exception as e:
        print(f"Error occured while testing chromadb")
        return False

if __name__ == "__main__":
  website_url = "https://www.tmeworldwide.com/"
  analyze_website(website_url)
  


