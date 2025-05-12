import openai
from openai import OpenAI
import requests
from config import OPENAI_API_KEY,AIRTABLE_API_KEY,AIRTABLE_BASE_ID,PERPLEXITY_API_KEY
import pinecone
from openai import OpenAI
import json

openai.api_key = OPENAI_API_KEY

class GuidelineGenerate:
    def classify_company_vertical(self):
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at classifying companies into business verticals. "
                                "Respond only with one of the following tags: advertising_agencies, media_companies, or brands. "
                                "If the company is not clearly an advertising_agency or a media_company, respond with 'brands'."
                    },
                    {
                        "role": "user",
                        "content": f"Given the following information about a lead's company:\n\n"
                                f"Industry: {self.industry}\n"
                                f"Description: {self.description}\n\n"
                                f"Classify the company into one of the following verticals based on the best fit:\n"
                                f"1) advertising_agencies\n"
                                f"2) media_companies\n"
                                f"3) brands\n\n"
                                f"Respond with only one of the tags as plain text: advertising_agencies, media_companies, or brands."
                    }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while classifying company: {e}")
            return "brands"

    def get_recent_achievements_person(self):
        try:
            url = "https://api.perplexity.ai/chat/completions"

            payload = {
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1,
                "web_search_options": {"search_context_size": "low"},
                "model": "sonar",
                "max_tokens": 2000,
                "messages": [
                    {
                        "content": (
                            "You are a professional assistant helping with lead research. "
                            "Your job is to extract recent achievements and activities of a person based on available data. "
                            "If external data (e.g. LinkedIn) is not accessible, summarize using the given employment summary and LinkedIn bio."
                        ),
                        "role": "system"
                    },
                    {
                        "role": "user",
                        "content": f"""
                                    These are some information about a prospective lead:
                                    Recipient's role: {self.recipient_role}
                                    Recipient's Name: {self.recipient_first_name} {self.recipient_last_name}
                                    Recipient's LinkedIn bio: {self.recipient_bio}
                                    Recipient's Employment Summary:
                                    {self.employment_summary}
                                    Recipient's Company Website: {self.recipient_company_website}

                                    Find information about this person through their LinkedIn.
                                    Search for {self.recipient_first_name} working at {self.recipient_company} on LinkedIn.

                                    Output:
                                    Only return the recipient's recent achievements and activities. If the information is not available, use the recipient's employment summary and LinkedIn bio. Do not include any other details or commentary.
                                    """
                    }
                ]
            }
            headers = {
                "Authorization": PERPLEXITY_API_KEY,
                "Content-Type": "application/json"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            print(response.text)
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error occurred while generating summary: {e}")
            return "No achievements found."


    def get_recent_achievements_company(self):
        try:
            url = "https://api.perplexity.ai/chat/completions"

            payload = {
                "temperature": 0.2,
                "top_p": 0.9,
                "return_images": False,
                "return_related_questions": False,
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1,
                "web_search_options": {"search_context_size": "low"},
                "model": "sonar",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional assistant skilled at corporate research. "
                                "Your task is to identify and summarize the latest achievements of a company based on a lead’s role and the company’s website."
                    },
                    {
                        "role": "user",
                        "content": f"These are some information about a prospective lead:\n"
                                f"Recipient's role: {self.recipient_role}\n"
                                f"Recipient's Company Website: {self.recipient_company_website}\n\n"
                                f"Find recent information related to this job role in the company associated with {self.recipient_first_name} {self.recipient_last_name}.\n\n"
                                f"Output:\n"
                                f"Please return the recipient's latest company's achievement."
                    }
                ]
            }

            headers = {
                "Authorization": PERPLEXITY_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            print(response.text)
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error occurred while generating summary: {e}")
            return "No achievements found."


    def generate_search_term_cvp_brands(self):
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages = [
                {
                    "role": "system",
                    "content": "You are helping generate a search term for a Pinecone vector database. The goal is to find relevant information from our knowledge base that can be used to craft a value proposition marketing email. Your response must consist only of the search term, with no extra commentary or formatting."
                },
                {
                    "role": "user",
                    "content": f"""You are tasked with creating a search term for our pinecone database. This information is going to be used to create a value proposition marketing email.

                    We're targeting a {self.industry} who is interested ONLY in our data product.

                    This is some news about the company that might be related to the recipient:
                    {self.about_company}

                    Please propose a search term to search our knowledge base. Make it specific to the recipient's industry. We want to find relevant information so we can present a very specific value proposition and features they would be interested in.

                    Your response should be purely the search term with nothing else. Don't put any line breakers."""
                }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while classifying company: {e}")
            return "brands"
        

    def generate_search_term_cvp_brands(self):
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages = [
                {
                    "role": "system",
                    "content": "You are helping generate a search term for a Pinecone vector database. The goal is to find relevant information from our knowledge base that can be used to craft a value proposition marketing email. Your response must consist only of the search term, with no extra commentary or formatting."
                },
                {
                    "role": "user",
                    "content": f"""You are tasked with creating a search term for our pinecone database. This information is going to be used to create a value proposition marketing email.

                    We're targeting a {self.industry} who is interested ONLY in our data product.

                    This is some news about the company that might be related to the recipient:
                    {self.about_company}

                    Please propose a search term to search our knowledge base. Make it specific to the recipient's industry. We want to find relevant information so we can present a very specific value proposition and features they would be interested in.

                    Your response should be purely the search term with nothing else. Don't put any line breakers."""
                }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while classifying company: {e}")
            return "brands"


    def generate_search_term_cvp_data_media(self):
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are helping generate a search term for a Pinecone vector database. The goal is to find relevant information from our knowledge base that can be used to craft a value proposition marketing email. Your response must consist only of the search term, with no extra commentary or formatting."
                    },
                    {
                        "role": "user",
                        "content": f"""You are tasked with creating a search term for our pinecone database. This information is going to be used to create a value proposition marketing email.

                        We're targeting a {self.industry} who is interested in our data and media planning products.

                        This is some news about the company that might be related to the recipient:
                        {self.about_company}

                        Please propose a search term to search our knowledge base. Make it specific to the recipient's industry. We want to find relevant information so we can present a very specific value proposition and features they would be interested in.

                        Your response should be purely the search term with nothing else. Don't put any line breakers."""
                    }
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error occurred while generating search term: {e}")
            return "data and media planning"

    def create_embedding_from_response_text(self,response_text):
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            embedding_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=response_text
            )
            return embedding_response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def query_top_k_from_pinecone(self,query_vector, top_k=5, namespace="", include_metadata=True):
        """
        Queries the Pinecone vector database to retrieve the top-k most similar items to the provided query vector.

        Parameters:
        - query_vector (list of float): The vector representation of your query.
        - top_k (int): The number of top similar items to retrieve.
        - namespace (str): The namespace within the Pinecone index to query.
        - include_metadata (bool): Whether to include metadata in the results.

        Returns:
        - list of dict: A list of dictionaries containing the ID, score, and metadata (if included) of the top-k similar items.
        """
        try:
            # Initialize Pinecone client
            pinecone.init(api_key="YOUR_PINECONE_API_KEY", environment="YOUR_PINECONE_ENVIRONMENT")

            # Connect to the Pinecone index
            index = pinecone.Index("YOUR_INDEX_NAME")

            # Perform the query
            response = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=include_metadata,
                namespace=namespace
            )

            # Extract and return the matches
            return response['matches']

        except Exception as e:
            print(f"An error occurred while querying Pinecone: {e}")
            return []

    def generate_customer_pain_point_term(self):
        """
        Generates a search term in JSON format to extract relevant pain points from the knowledge base.

        Parameters:
        - recipient_first_name (str): First name of the recipient.
        - recipient_role (str): Role of the recipient.
        - recipient_company (str): Company where the recipient works.
        - recipient_bio (str): Bio of the recipient.
        - company_news (str): Recent news about the recipient's company.
        - additional_info (str): Additional information about the recipient.

        Returns:
        - dict: A dictionary containing the search term.
        """
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            prompt = f"""
            You're an expert at writing marketing emails. You're tasked with writing an email to this recipient: {self.recipient_first_name} who works as {self.recipient_role} at {self.recipient_company}.

            This is some information we know about them:
            {self.additional_info}
            {self.recipient_bio}

            This is some news about the company that might be related to the recipient:
            {self.company_news}

            Before writing this email, we are going to go to our knowledge base and extract relevant information that we can present to this lead.

            Based on the lead's role and industry, please propose a search term to search our knowledge base to extract pain points we can solve for them.
            Respond in JSON

            {{
            "search_term": ""
            }}
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates search terms in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"An error occurred while generating the search term: {e}")
            return {"search_term": ""}
        

    def generate_b2b_sales_email(self):
        """
        Generates a persuasive B2B sales email for Guideline.ai targeting a specific recipient.

        Parameters:
        - recipient_first_name (str): First name of the recipient.
        - recipient_last_name (str): Last name of the recipient.
        - recipient_role (str): Role of the recipient.
        - recipient_company (str): Company where the recipient works.
        - target_industry (str): Industry of the target company.
        - competitor_company (str): Competitor company name.
        - key_pain_points (str): Key pain points in JSON format.
        - value_proposition (str): Key benefit or value proposition.

        Returns:
        - dict: A dictionary containing the structured email content.
        """
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            prompt = f"""
            Generate a persuasive B2B sales email for Guideline.ai targeting {self.recipient_first_name} {self.recipient_last_name}, a {self.recipient_role} at {self.recipient_company}. The email should be structured to engage the recipient, highlight key benefits, and prompt a response.

            ### Input Variables:
            - **Target company:** {self.recipient_company}
            - **Target industry:** {self.target_industry}
            - **Competitor company:** {self.competitor_company}
            - **Target role:** {self.recipient_role}
            - **Product/service:** Guideline.ai
            - **Key pain points:** {self.key_pain_points}
            - **Key benefit:** 
            {self.value_proposition}
            ---

            ### Email Structure:

            #### 1. Subject Line:
            - References the **target company** by name
            - Creates **urgency or curiosity**
            - Hints at a **competitive advantage or efficiency gain**
            - Limited to **50-60 characters**

            #### 2. Email Body:
            - **Paragraph 1: Personalized Context (2-3 sentences)**
            - No greetings or recipient’s name.
            - Reference a **recent company announcement, initiative, or industry trend** specific to the recipient.
            - Show **research** into their current situation.
            - Identify a **challenge or opportunity** they are likely facing.

            - **Paragraph 2: Value Proposition (2-3 sentences)**
            - Introduce **Guideline.ai** as a solution to their challenge.
            - If the target industry is a brand or advertising agency, highlight insights related to **media planning and ad spend data**. If it’s a media company, focus only on **ad spend data** and omit any mention of media planning.
            - Include a **specific, quantifiable benefit** (e.g., percentages or efficiency gains).
            - Focus on **business outcomes, not features**.

            - **Paragraph 3: Social Proof (2-3 sentences)**
            - Mention a **relevant competitor or industry peer** who uses Guideline.ai.
            - Include a **specific result** they achieved.
            - Frame it as an **advantage the recipient is currently missing**.

            - **Paragraph 4: Call-to-Action (2 sentences)**
            - Request a time this week or early next week (**15-minute call**).
            - Create **slight urgency** without being pushy.

            ### Tone Guidelines

            - Professional but conversational
            - Confident without being arrogant
            - Direct without being aggressive
            - Focused on their business outcomes, not your product features
            - Slightly urgent without seeming desperate
            - Demonstrate insider knowledge of their industry

            ### OUTPUT FORMAT
            The response **must** be in **pure JSON text format** as the one given below with no additional text:

            {{
            "subject": "",
            "ice_breaker": "",
            "client_value_proposition": "",
            "case_studies": "",
            "call_to_action": ""
            }}
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert B2B sales copywriter. Generate the email content in pure JSON format as specified."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"An error occurred while generating the sales email: {e}")
            return {
                "subject": "",
                "ice_breaker": "",
                "client_value_proposition": "",
                "case_studies": "",
                "call_to_action": ""
            }

    def optimize_linkedin_outreach_message(self):
        """
        Optimizes LinkedIn outreach message sections based on provided information.

        Parameters:
        - ice_breaker (str): The initial engaging hook.
        - client_value_proposition (str): The value propositions of the client.
        - case_studies (str): Relevant case studies or success stories.
        - call_to_action (str): The call to action prompting a response.

        Returns:
        - dict: A dictionary containing the optimized LinkedIn message components.
        """
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            prompt = f"""
            Optimize the following LinkedIn outreach message sections based on the provided information. Ensure each section is **concise, engaging, and formatted for LinkedIn** while keeping the core message intact.

            ### PROVIDED INFORMATION:
            - **Ice Breaker:** {self.ice_breaker}
            - **Client Value Propositions:** {self.client_value_proposition}
            - **Case Studies:** {self.case_studies}
            - **Call to Action:** {self.call_to_action}

            ### TASK:
            Refine and restructure the content while preserving the core message:

            1. **Ice Breaker (Engaging Hook)**
            - **Remove greetings or recipient names.**
            - Keep it **concise** while maintaining personalization and relevance.

            2. **About Company**
            - **Summarize and condense** the provided value propositions and case studies.
            - Highlight the **most relevant** aspects in a clear, impactful way and summarize it into one concise short section.

            3. **Call to Action (CTA)**
            - Ensure it is **direct, compelling, and encourages a response**.
            - Maintain a **conversational and professional tone**.

            4. **LinkedIn Subject**
            - Craft a **concise, curiosity-driven subject** that improves engagement.

            ### OUTPUT FORMAT
            The response **must** be in **pure string JSON format** as the one given below with no additional text:
            "{{
            "ice_breaker_linkedin": "",
            "about_company_linkedin": "",
            "call_to_action_linkedin": "",
            "linkedin_subject": ""
            }}"

            ### KEY REQUIREMENTS:
            ✅ **Do not generate new content**—only **restructure and optimize** existing information.  
            ✅ Ensure the response is **brief, engaging, and LinkedIn-friendly**.  
            ✅ **No greetings or recipient names** should be included.  
            ✅ **Strictly return a JSON-formatted response with no additional text.**
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional LinkedIn outreach copywriter. Optimize the provided content into LinkedIn-friendly formats."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"An error occurred while optimizing the LinkedIn message: {e}")
            return {
                "ice_breaker_linkedin": "",
                "about_company_linkedin": "",
                "call_to_action_linkedin": "",
                "linkedin_subject": ""
            }
        

    def generate_follow_up_email_sections(self):
        """
        Generates a concise and professional follow-up email in JSON format.

        Parameters:
        - ice_breaker (str): The initial engaging hook.
        - about_company (str): Information about the company.
        - call_to_action (str): The call to action prompting a response.
        - previous_email_subject (str): The subject line of the previous email.

        Returns:
        - dict: A dictionary containing the follow-up email components.
        """
        client = OpenAI(api_key=OPENAI_API_KEY)
        try:
            prompt = f"""
            Generate a concise and professional follow-up email sections using the given details.

            ### **Available Information:**
            - **Ice Breaker:** {self.ice_breaker}
            - **About Company:** {self.about_company}
            - **Call to Action:** {self.call_to_action}  
            - **Previous Email Subject:** {self.previous_email_subject}  

            ### **Requirements:**
            1. Ensure the **tone is professional, friendly, and concise**, maintaining the context of a follow-up.  
            2. Provide a **reworded subject line** that aligns with the follow-up nature.  
            3. **Output Format:** A pure JSON string with the following keys:  
            - "ice_breaker_follow_up": Personalized follow-up opening line. 
                (Do not include greetings or recipient name)
            - "about_company_follow_up": A short, compelling summary of the about section of the company.
            - "call_to_action_follow_up": A follow-up request that is clear, inviting, and action-driven.  
            - "subject_follow_up": A refined, engaging follow-up subject line.  

            ### OUTPUT FORMAT
            The response **must** be in **pure JSON format** as the one given below with no additional text:
            "{{
            "ice_breaker_follow_up": "",
            "about_company_follow_up": "",
            "call_to_action_follow_up": "",
            "subject_follow_up": ""
            }}"

            The output should be pure JSON text without "json" before it.
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional email copywriter specializing in crafting concise and effective follow-up emails."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except Exception as e:
            print(f"An error occurred while generating the follow-up email: {e}")
            return {
                "ice_breaker_follow_up": "",
                "about_company_follow_up": "",
                "call_to_action_follow_up": "",
                "subject_follow_up": ""
            }
        
    def generate_follow_up_linkedin_message(self):
            """
            Generates a concise and professional follow-up LinkedIn message in JSON format.

            Parameters:
            - ice_breaker (str): The initial engaging hook.
            - about_company (str): Information about the company.
            - call_to_action (str): The call to action prompting a response.
            - previous_email_subject (str): The subject line of the previous email.

            Returns:
            - dict: A dictionary containing the follow-up LinkedIn message components.
            """
            try:
                prompt = f"""
                Generate a concise and professional follow-up LinkedIn message sections using the given details.

                ### **Available Information:**
                - **Ice Breaker:** {self.ice_breaker}
                - **About Company:** {self.about_company}
                - **Call to Action:** {self.call_to_action}  
                - **Previous Email Subject:** {self.previous_email_subject}  

                ### **Requirements:**
                1. **Rephrase** the about company section to be used for a suitable follow-up message for LinkedIn.  
                2. Ensure the **tone is professional, friendly, and concise**, maintaining the context of a follow-up.  
                3. Provide a **reworded subject line** that aligns with the follow-up nature.  
                4. **Output Format:** A pure JSON string with the following keys:  
                - "ice_breaker_linkedin_follow_up": Personalized follow-up opening line. 
                - "about_company_linkedin_follow_up": A short, compelling summary of the provided about section.
                - "call_to_action_linkedin_follow_up": A follow-up request that is clear, inviting, and action-driven.  
                - "subject_linkedin_follow_up": A refined, engaging follow-up subject line.  

                ### OUTPUT FORMAT
                The response **must** be in **pure JSON format** as the one given below with no additional text:
                "{{
                "ice_breaker_linkedin_follow_up": "",
                "about_company_linkedin_follow_up": "",
                "call_to_action_linkedin_follow_up": "",
                "subject_linkedin_follow_up": ""
                }}"

                The output should be pure JSON text without "json" before it.
                """
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional LinkedIn message copywriter specializing in crafting concise and effective follow-up messages."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                )
                content = response.choices[0].message.content.strip()
                return json.loads(content)
            except Exception as e:
                print(f"An error occurred while generating the follow-up LinkedIn message: {e}")
                return {
                    "ice_breaker_linkedin_follow_up": "",
                    "about_company_linkedin_follow_up": "",
                    "call_to_action_linkedin_follow_up": "",
                    "subject_linkedin_follow_up": ""
                }

    def generate_connection_message(self):
            """
            Generates a concise and professional LinkedIn connection request message in JSON format.

            Parameters:
            - ice_breaker (str): Personalized opening line without greeting or recipient name.
            - about_company (str): Info about the company to be rephrased into one compelling sentence.
            - call_to_action (str): Action-oriented request.
            - previous_email_subject (str): Prior subject line to help shape the new subject.

            Returns:
            - dict: A dictionary with connection message components in JSON format.
            """
            try:
                prompt = f"""
                Generate a concise and professional LinkedIn connection request message sections using the given details.

                ### **Available Information:**
                - **Ice Breaker:** {self.ice_breaker}
                - **About Company:** {self.about_company}
                - **Call to Action:** {self.call_to_action}
                - **Previous Email Subject:** {self.previous_email_subject}

                ### **Requirements:**
                1. Rephrase the about section into a single brief and compelling sentence for LinkedIn connection request.
                2. Ensure the tone is professional, friendly, and concise.
                3. Provide a reworded subject line that aligns with a LinkedIn connection request.

                ### OUTPUT FORMAT
                The response must be in pure JSON format as shown below with no additional text:
                {{
                "ice_breaker_connection_message": "",
                "about_company_connection_message": "",
                "call_to_action_connection_message": "",
                "subject_connection_message": ""
                }}
                """
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional LinkedIn message copywriter."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                )
                content = response.choices[0].message.content.strip()
                return json.loads(content)

            except Exception as e:
                print(f"Error generating connection message: {e}")
                return {
                    "ice_breaker_connection_message": "",
                    "about_company_connection_message": "",
                    "call_to_action_connection_message": "",
                    "subject_connection_message": ""
                }


    def generate_linkedin_connection_message(self):
        """
        Generates a concise LinkedIn connection request message from the provided email content.

        Parameters:
        - email_content (str): The content of the email to base the LinkedIn message on.
        - api_key (str): Your OpenAI API key.

        Returns:
        - str: A LinkedIn connection message not exceeding 220 characters.
        """

        prompt = f"""
        Task:
        Generate a concise LinkedIn connection request message based on the content from the provided email.

        Source:
        - Email content: {self.email_content}

        Objective:
        - Create a short, professional, and persuasive LinkedIn connection message that fits within LinkedIn’s 220-character limit.

        Requirements:
        - Strictly maximum 220 characters (not even 221)
        - Start with a greeting
        - Keep it brief, clear, and value-driven
        - Add a light, personable icebreaker
        - Use only the provided email content, no external or unrelated details
        - Do not include a signature or closing line

        Output:
        - Only return the final LinkedIn message in plain text. Do not exceed 220 characters under any circumstance.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional copywriter specializing in LinkedIn outreach."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )

            message = response['choices'][0]['message']['content'].strip()

            if len(message) > 220:
                raise ValueError("Generated message exceeds 220 characters.")

            return message

        except Exception as e:
            print(f"Error: {e}")
            return ""