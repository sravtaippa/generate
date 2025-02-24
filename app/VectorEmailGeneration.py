import os
import json
import pinecone
from openai import OpenAI
from typing import Dict, List, Any


class EmailGenerator:
    def __init__(self, openai_api_key: str, pinecone_api_key: str, pinecone_env: str = "us-east-1"):
        """
        Initialize the Email Generator with API keys and environment variables
        """
        # Set up OpenAI client
        self.openai_client = OpenAI(api_key=openai_api_key)

        # Set up Pinecone
        self.pc = pinecone.Pinecone(api_key=pinecone_api_key)
        self.pinecone_env = pinecone_env
        self.index_name = "webanalysis"  # Replace with your actual index name
        self.index = self.pc.Index(self.index_name)

    def get_recipient_info(self, recipient_email: str, recipient_name: str, recipient_company: str) -> Dict:
        """
        Query Pinecone to get information about the recipient
        """
        # Generate an embedding for the recipient using OpenAI
        query_embedding = self._generate_embedding(
            f"Recipient: {recipient_name}, Company: {recipient_company}, Email: {recipient_email}"
        )

        # Query Pinecone with the embedding
        query_results = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )

        # Extract and process the results
        recipient_info = {
            "name": recipient_name,
            "email": recipient_email,
            "company": recipient_company,
            "additional_info": {}
        }

        # Process and merge metadata from results
        for match in query_results.matches:
            if match.score < 0.7:  # Skip low relevance matches
                continue

            metadata = match.metadata
            if "role" in metadata and "role" not in recipient_info:
                recipient_info["role"] = metadata["role"]

            if "bio" in metadata:
                recipient_info["bio"] = metadata["bio"]

            if "company_info" in metadata:
                recipient_info["company_info"] = metadata["company_info"]

            # Add any other fields to additional_info
            for key, value in metadata.items():
                if key not in ["role", "bio", "company_info"] and key not in recipient_info:
                    recipient_info["additional_info"][key] = value

        return recipient_info

    def get_sender_info(self, sender_email: str, sender_name: str, sender_company: str) -> Dict:
        """
        Query Pinecone to get information about the sender
        """
        # Generate an embedding for the sender using OpenAI
        query_embedding = self._generate_embedding(
            f"Sender: {sender_name}, Company: {sender_company}, Email: {sender_email}"
        )

        # Query Pinecone with the embedding
        query_results = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )

        # Extract and process the results
        sender_info = {
            "name": sender_name,
            "email": sender_email,
            "company": sender_company,
            "additional_info": {}
        }

        # Process and merge metadata from results
        for match in query_results.matches:
            if match.score < 0.7:  # Skip low relevance matches
                continue

            metadata = match.metadata
            if "role" in metadata and "role" not in sender_info:
                sender_info["role"] = metadata["role"]

            if "value_proposition" in metadata:
                sender_info["value_proposition"] = metadata["value_proposition"]

            if "company_info" in metadata:
                sender_info["company_info"] = metadata["company_info"]

            if "company_website" in metadata:
                sender_info["company_website"] = metadata["company_website"]

            # Add any other fields to additional_info
            for key, value in metadata.items():
                if key not in ["role", "value_proposition", "company_info",
                               "company_website"] and key not in sender_info:
                    sender_info["additional_info"][key] = value

        return sender_info

    def research_recipient(self, recipient_info: Dict) -> Dict:
        """
        Enhance recipient information with additional online research
        """
        # Construct a prompt to research the recipient
        research_prompt = f"""
        I need you to search and provide detailed information about this person:

        Name: {recipient_info.get('name', 'Unknown')}
        Company: {recipient_info.get('company', 'Unknown')}
        Role: {recipient_info.get('role', 'Unknown')}
        Bio: {recipient_info.get('bio', 'Not available')}

        Please provide:
        1. A professional persona description
        2. Educational background
        3. Career highlights
        4. Recent activities or interests
        5. Any notable achievements

        Format the results as JSON with these fields: persona, education, career_highlights, recent_activities, achievements
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a research specialist who analyzes professional profiles. Return results in valid JSON format."},
                {"role": "user", "content": research_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content

        # Extract JSON from the response
        try:
            # Find JSON in the response (looking for opening/closing braces)
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                research_data = json.loads(result_text[json_start:json_end])
            else:
                # If JSON formatting failed, create a basic structure
                research_data = {
                    "persona": "Could not extract persona information",
                    "education": "Unknown",
                    "career_highlights": "Not available",
                    "recent_activities": "Not available",
                    "achievements": "Not available"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            research_data = {
                "persona": "Could not extract persona information",
                "education": "Unknown",
                "career_highlights": "Not available",
                "recent_activities": "Not available",
                "achievements": "Not available"
            }

        # Merge research data with recipient info
        recipient_info.update(research_data)
        return recipient_info

    def generate_email_template(self, domain: str, business_type: str) -> str:
        """
        Generate an email template structure based on domain and business type
        """
        template_prompt = f"""
        You're a cold outreach expert in the {domain} domain.

        Create the best cold outreach email template structure for a {business_type} campaign.
        What should the structure and format of the email body be? Use industry best practices
        to maximize open rates, click-through rates, and conversion rates.

        Return a detailed template structure with placeholders.
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert email marketer specializing in cold outreach."},
                {"role": "user", "content": template_prompt}
            ],
            temperature=1.0,
            max_tokens=2000
        )

        return response.choices[0].message.content

    def generate_email_prompt(self, recipient_info: Dict, sender_info: Dict, template: str,
                              domain: str, business_type: str, cta_options: str) -> str:
        """
        Create a comprehensive prompt for email generation
        """
        prompt = f"""
        Create a complete cold outreach email that will maximize open rates, clickthrough rates and conversion rates.

        Language Guidelines:
        - The language should be polarizing and call for action.
        - The email should be in the language that relates to the recipient and their industry.

        Recipient Information:
        - Name: {recipient_info.get('name', 'Unknown')}
        - Role: {recipient_info.get('role', 'Unknown')}
        - Company: {recipient_info.get('company', 'Unknown')}
        - Bio: {recipient_info.get('bio', 'Not available')}
        - Persona: {recipient_info.get('persona', 'Not available')}
        - Education: {recipient_info.get('education', 'Not available')}
        - Recent Activities: {recipient_info.get('recent_activities', 'Not available')}

        Sender Information:
        - Name: {sender_info.get('name', 'Unknown')}
        - Title: {sender_info.get('role', 'Unknown')}
        - Company: {sender_info.get('company', 'Unknown')}
        - Email: {sender_info.get('email', 'Unknown')}
        - Website: {sender_info.get('company_website', 'Unknown')}
        - Value Proposition: {sender_info.get('value_proposition', 'Not available')}
        - Domain: {domain}
        - Business Type: {business_type}
        - CTA Options: {cta_options}

        Template to follow:
        {template}

        The email should have a subject line, personalized ice breaker, relevant value proposition, and clear call-to-action.
        Do not leave any placeholders or variables unfilled.
        """

        return prompt

    def generate_email(self, prompt: str) -> Dict:
        """
        Generate the final email based on the comprehensive prompt
        """
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a professional email writer. Always return responses in valid JSON format with subject and body fields."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content

        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                email_data = json.loads(result_text[json_start:json_end])
            else:
                # If JSON format not found, create a basic structure
                email_data = {
                    "subject": "Follow-up on our potential collaboration",
                    "body": result_text.strip()
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            email_data = {
                "subject": "Follow-up on our potential collaboration",
                "body": result_text.strip()
            }

        return email_data

    def format_html_email(self, email_data: Dict, font_style: str, color_scheme: str) -> Dict:
        """
        Format the email as HTML with styling
        """
        html_prompt = f"""
        Using the email body below, create an HTML email with inline CSS using style attributes for visual appeal. 
        Only use INLINE CSS and DO NOT USE INTERNAL CSS.

        Include: Font: {font_style} which is clean and professional
        Use color scheme: {color_scheme}

        Proper spacing (e.g., padding and line height) for readability.
        Highlighted key points with bold text or subtle background colors.
        A styled CTA button with clear and readable text.
        The email should look highly professional and organized.
        The email should have a clean border.
        Focus on readability on mobile devices.

        Email Body:
        Subject: {email_data.get('subject', 'No subject')}

        {email_data.get('body', 'No content')}

        The output must be a valid JSON object with 'subject' and 'emailBodyHTML' fields.
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are an HTML email designer. Return only valid JSON with subject and emailBodyHTML fields."},
                {"role": "user", "content": html_prompt}
            ],
            temperature=0.2,
            max_tokens=4000
        )

        result_text = response.choices[0].message.content

        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                html_email = json.loads(result_text[json_start:json_end])
            else:
                # If JSON format not found, create a basic structure
                html_email = {
                    "subject": email_data.get('subject', 'No subject'),
                    "emailBodyHTML": f"<html><body>{email_data.get('body', 'No content')}</body></html>"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            html_email = {
                "subject": email_data.get('subject', 'No subject'),
                "emailBodyHTML": f"<html><body>{email_data.get('body', 'No content')}</body></html>"
            }

        return html_email

    def generate_follow_up_email(self, original_email: Dict, value_proposition: str) -> Dict:
        """
        Generate a follow-up email based on the original email
        """
        follow_up_prompt = f"""
        You are generating a professional follow-up email to send if no response was received.

        The follow-up should:
        1. Remind the recipient of the previous email
        2. Express understanding of their busy schedule
        3. Highlight additional key benefits: {value_proposition}
        4. Be action-oriented with a clear CTA
        5. Maintain the same styling and formatting

        Previous email: 
        {original_email.get('emailBodyHTML', 'No content')}

        The output should be JSON with a 'followUpHTML' field containing the HTML email.
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are a follow-up email specialist. Return only valid JSON with a followUpHTML field."},
                {"role": "user", "content": follow_up_prompt}
            ],
            temperature=1.0,
            max_tokens=4000
        )

        result_text = response.choices[0].message.content

        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                follow_up_email = json.loads(result_text[json_start:json_end])
            else:
                # If JSON format not found, create a basic structure
                follow_up_email = {
                    "followUpHTML": f"<html><body>Following up on my previous email. Would you be available for a quick discussion?</body></html>"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            follow_up_email = {
                "followUpHTML": f"<html><body>Following up on my previous email. Would you be available for a quick discussion?</body></html>"
            }

        return follow_up_email

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text using OpenAI
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding


def main():
    # Get API keys from environment (for security)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY",
                                 "pcsk_4grhx7_9JekVGgbgZH4mA6KdqLpMmVvy9DJCw2LfxzWW6y2SbpLpgvTzZSauacTcs4kfyA")
    pinecone_env = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    # Initialize the email generator
    email_gen = EmailGenerator(openai_api_key, pinecone_api_key, pinecone_env)

    # Example usage
    recipient_email = "john.doe@example.com"
    recipient_name = "John Doe"
    recipient_company = "Acme Inc"

    sender_email = "sales@mycompany.com"
    sender_name = "Jane Smith"
    sender_company = "My Company"

    # Get information from Pinecone
    recipient_info = email_gen.get_recipient_info(recipient_email, recipient_name, recipient_company)
    sender_info = email_gen.get_sender_info(sender_email, sender_name, sender_company)

    # Enhanced research
    recipient_info = email_gen.research_recipient(recipient_info)

    # Generate email template
    domain = "SaaS"
    business_type = "B2B Sales"
    template = email_gen.generate_email_template(domain, business_type)

    # Generate email prompt
    cta_options = "Schedule a demo,Download whitepaper"
    prompt = email_gen.generate_email_prompt(recipient_info, sender_info, template, domain, business_type, cta_options)

    # Generate email content
    email_data = email_gen.generate_email(prompt)

    # Format as HTML
    font_style = "Arial, sans-serif"
    color_scheme = "#000000,#ffffff,#4a90e2,#f5f5f5"
    html_email = email_gen.format_html_email(email_data, font_style, color_scheme)

    # Generate follow-up email
    value_proposition = "Our solution reduces operational costs by 30% while improving efficiency by 25%"
    follow_up_email = email_gen.generate_follow_up_email(html_email, value_proposition)

    # Print the results
    print("Original Email Subject:", html_email.get("subject"))
    print("\nOriginal Email HTML:")
    print(html_email.get("emailBodyHTML")[:500] + "...\n")

    print("Follow-up Email HTML:")
    print(follow_up_email.get("followUpHTML")[:500] + "...\n")

    return {
        "original_email": html_email,
        "follow_up_email": follow_up_email
    }


if __name__ == "__main__":
    main()