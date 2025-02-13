"""
Email Generation System - Complete Implementation
Matches all Make.com scenario functionality including multiple table management,
robust error handling, and complete workflow alignment.
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from time import sleep
import openai
import colorama
from colorama import Fore, Style
import requests
import json
from typing import Dict

# Initialize colorama
colorama.init()

class DebugLogger:
    def __init__(self, name: str):
        self.name = name

    def info(self, message: str):
        print(f"{Fore.GREEN}[INFO] {self.name}: {message}{Style.RESET_ALL}")

    def debug(self, message: str):
        print(f"{Fore.BLUE}[DEBUG] {self.name}: {message}{Style.RESET_ALL}")

    def error(self, message: str):
        print(f"{Fore.RED}[ERROR] {self.name}: {message}{Style.RESET_ALL}")

    def success(self, message: str):
        print(f"{Fore.GREEN}[SUCCESS] {self.name}: {message}{Style.RESET_ALL}")

    def warning(self, message: str):
        print(f"{Fore.YELLOW}[WARNING] {self.name}: {message}{Style.RESET_ALL}")

    def step(self, message: str):
        print(f"{Fore.CYAN}[STEP] {self.name}: {message}{Style.RESET_ALL}")

@dataclass
class LeadData:
    unique_id: str
    recipient_first_name: str
    recipient_last_name: str
    recipient_role: str
    recipient_company: str
    recipient_email: str
    recipient_bio: Optional[str] = None
    employment_summary: Optional[str] = None
    associated_client_id: Optional[str] = None
    outreach_table: Optional[str] = None
    sender_name: Optional[str] = None
    sender_title: Optional[str] = None
    sender_company: Optional[str] = None
    sender_email: Optional[str] = None
    sender_company_website: Optional[str] = None
    key_benefits: Optional[str] = None
    unique_features: Optional[str] = None
    impact_metrics: Optional[str] = None
    cta_options: Optional[str] = None
    color_scheme: Optional[str] = None
    font_style: Optional[str] = None

class RetryHandler:
    """Handles retrying operations with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: int = 15):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.logger = DebugLogger("RetryHandler")

    def retry_operation(self, operation_func, *args, **kwargs):
        """Retries an operation with exponential backoff"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries - 1:
                    raise e

                delay = self.base_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                sleep(delay)

        if last_exception:
            raise last_exception

class AirtableManager:
    def __init__(self, api_key: str, base_id: str):
        self.logger = DebugLogger("Airtable")
        self.api_key = api_key
        self.base_id = base_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger.success("Initialized AirtableManager")

    def get_new_leads(self, table_name: str) -> List[Dict]:
        """Gets new leads from the specified table"""
        self.logger.step("Fetching new leads")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"

        one_day_ago = (datetime.now(timezone.utc)
                      .replace(hour=0, minute=0, second=0, microsecond=0)
                      .isoformat())

        params = {
            'filterByFormula': f"IS_AFTER({{created_date}}, '{one_day_ago}')",
            'maxRecords': 15,
            'sort[0][field]': 'created_date',
            'sort[0][direction]': 'desc'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get('records', [])
            self.logger.success(f"Found {len(records)} new leads")
            return records
        except Exception as e:
            self.logger.error(f"Error getting leads: {e}")
            return []

    def get_client_details(self, client_id: str) -> Optional[Dict]:
        """Gets client details from the client_info table"""
        self.logger.step(f"Getting client details for {client_id}")
        url = f"https://api.airtable.com/v0/{self.base_id}/client_info"

        params = {
            'filterByFormula': f"{{client_id}} = '{client_id}'",
            'maxRecords': 1
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            records = response.json().get('records', [])
            if records:
                self.logger.success("Found client details")
                return records[0]
            self.logger.warning("No client details found")
            return None
        except Exception as e:
            self.logger.error(f"Error getting client details: {e}")
            return None

    def create_record(self, table_name: str, fields: Dict) -> Optional[str]:
        """Creates a new record in specified table"""
        self.logger.step(f"Creating record in {table_name}")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"

        try:
            payload = {
                'records': [{
                    'fields': fields
                }]
            }
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            record_id = response.json()['records'][0]['id']
            self.logger.success(f"Created record {record_id}")
            return record_id
        except Exception as e:
            self.logger.error(f"Error creating record: {e}")
            return None

    def update_record(self, table_name: str, record_id: str, fields: Dict) -> bool:
        """Updates an existing record"""
        self.logger.step(f"Updating record {record_id}")
        url = f"https://api.airtable.com/v0/{self.base_id}/{table_name}/{record_id}"

        try:
            response = requests.patch(url, headers=self.headers, json={'fields': fields})
            response.raise_for_status()
            self.logger.success(f"Updated record {record_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating record: {e}")
            return False

class PerplexityEnricher:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("Perplexity")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger.success("Initialized PerplexityEnricher")

    def enrich_lead(self, lead: LeadData) -> str:
        """Enriches lead data with additional research"""
        self.logger.step(f"Enriching lead data for {lead.recipient_first_name}")
        url = "https://api.perplexity.ai/chat/completions"

        prompt = f"""
        Information about lead:
        Role: {lead.recipient_role}
        Name: {lead.recipient_first_name} {lead.recipient_last_name}
        Bio: {lead.recipient_bio}
        Company: {lead.recipient_company}
        Employment: {lead.employment_summary}

        Search about this person and their company on the internet and social media pages.
        Find information that can be used as an ice breaker for cold email outreach.
        Focus on recent achievements, company news, or professional interests.
        """

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={
                    "model": "llama-3.1-sonar-huge-128k-online",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"Error enriching lead: {e}")
            return ""


class EmailGenerator:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("EmailGen")
        self.api_key = api_key
        openai.api_key = api_key
        self.logger.success("Initialized EmailGenerator")

    def _get_email_template(self, domain: str, business_type: str) -> str:
        """Gets optimal email template structure for the domain"""
        prompt = f"""You're an cold outreach expert in the {domain} domain working in Dubai, U.A.E

You're tasked with producing the best cold outreach email template for a campaign. What should the structure and the format of the email body be. Use all the industry best practices in {business_type} marketing to generate the ideal template and structure to maximize open rates, click through rates and conversion rates.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting template: {e}")
            return ""

    def generate_content(self, lead: LeadData, client_data: Dict, enriched_data: str) -> Dict[str, str]:
        """Generates email content using the template"""
        self.logger.step(f"Generating email for {lead.recipient_first_name}")

        # First get optimal template
        template = self._get_email_template(
            client_data.get('domain', ''),
            client_data.get('business_type', '')
        )

        try:
            # Generate email generation prompt
            prompt = f"""You're an expert prompt engineer and cold outreach copy writer.

Generate a prompt that will generate a complete cold outreach email that will maximize open rates, clickthrough rates and conversion rates. The email generated should cover everything from the subject to the signoff in the email. The prompt should use the information provided below and not hallucinate additional information or require additional information.

Below is the information about the recipient of the email:
Recipient's Role: {lead.recipient_role}
Recipient's Name: {lead.recipient_first_name} {lead.recipient_last_name}
Recipient's LinkedIn bio: {lead.recipient_bio}
Recipient's Employment Summary: {lead.employment_summary}

More information about recipient: {enriched_data}

Below is the information about the sender of the email (only use this information in the footer of the email):
Sender name: {lead.sender_name}
Sender Title: {lead.sender_title}
Sender Company: {lead.sender_company}
Sender Email: {lead.sender_email}
Sender Website: {lead.sender_company_website}
Sender Product's key benefits: {lead.key_benefits}
Sender Product's unique selling points: {lead.unique_features}
Sender's Social Proof: {lead.impact_metrics}
Sender's preferred CTA: {lead.cta_options}
Sender's Client: {client_data.get('business_type', '')}
Sender's Domain: {client_data.get('domain', '')}
Sender's Business Model: {client_data.get('business_type', '')}

Below is the template the email should follow:
{template}

Make sure you include all the relevant information such as sender and Recipient information.

Language Guidelines:
Make sure the language is polarizing and strong.
Speak the language of the Recipient use their jargons and lingo to better relate to them.

Your output should only be the prompt and nothing else. The email should not have any empty name spaces or variables that are not provided. Do not hallucinate information or use information not provided. Utilize only the information available."""

            # Get the prompt for email generation
            prompt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,
                max_tokens=4000
            )

            # Use the generated prompt to create the actual email
            email_prompt = f"""{prompt_response.choices[0].message.content}

The email should not have unfilled name spaces write the complete email only with only the information provided. Do not leave variable names or spaces that need to be filled in."""

            email_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": email_prompt}],
                temperature=1.0,
                max_tokens=4000
            )

            # Generate HTML version with styling
            html_prompt = f"""Using the email body below, create an HTML email with inline CSS using style attributes for visual appeal. Only use INLINE CSS and DO NOT USE INTERNAL CSS.

Include: Font: {lead.font_style} which is Clean and professional and use the color scheme {lead.color_scheme}

Proper spacing (e.g., padding and line height) for readability. Highlighted key points with bold text or subtle background colors. A styled CTA button with clear and readable text. The email should look highly professional and organized. The email should have a clean border. Do not make the email extravagant and focus on readability on mobile devices.

Email Body: {email_response.choices[0].message.content}

The output should be only purely JSON text without formatting and without writing json before the actual json code.
{{
    "subject":"",
    "emailBodyHTML":""
}}"""

            html_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": html_prompt}],
                temperature=1.0,
                max_tokens=4000
            )

            # Generate follow-up email
            followup_prompt = f"""You are an AI agent that generates professional follow-up emails. Your task is to create a polite and engaging follow-up email to send if no response was received after a specified period. The follow-up should remind the recipient of the previous email, express understanding of their busy schedule, and encourage a response while maintaining professionalism.

The follow up email should highlight some of the key benefits: {lead.key_benefits}
or unique feature: {lead.unique_features}
that have not been already highlighted in the previous email.

The email should be action oriented and have a clear CTA.

The Email should be in HTML and Inline CSS follow the same color scheme, fonts and design from the previous email sent.

The output should be only purely JSON text without formatting and without writing json before the actual json code.
{{
    "followUpHTML":""
}}

Below is the previous email sent:
{html_response.choices[0].message.content}"""

            followup_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": followup_prompt}],
                temperature=1.0,
                max_tokens=4000
            )

            # Parse response into JSON format
            try:
                html_content = json.loads(html_response.choices[0].message.content)
                followup_content = json.loads(followup_response.choices[0].message.content)

                email_content = {
                    "Subject": html_content.get("subject", ""),
                    "Email_Body": html_content.get("emailBodyHTML", ""),
                    "Follow_up": followup_content.get("followUpHTML", "")
                }

                self.logger.success("Generated email content")
                return email_content
            except json.JSONDecodeError as je:
                self.logger.error(f"JSON parsing error: {je}")
                return {}

        except Exception as e:
            self.logger.error(f"Error generating email: {str(e)}")
            return {}


class InstantlyManager:
    def __init__(self, api_key: str):
        self.logger = DebugLogger("Instantly")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.instantly.ai/api/v2"
        self.logger.success("Initialized InstantlyManager")

    def add_to_campaign(self, campaign_id: str, lead: 'LeadData', email_content: Dict[str, str]) -> bool:
        """Adds a lead to an email campaign"""
        url = f"{self.base_url}/leads"

        # Prepare the payload according to working API format
        payload = {
            "campaign": campaign_id,
            "email": lead.recipient_email,
            "first_name": lead.recipient_first_name,
            "last_name": lead.recipient_last_name,
            "company_name": lead.recipient_company,
            "personalization": f"Hi {{{{first_name}}}}, I noticed your work at {{{{company_name}}}}",
            "website": lead.sender_company_website or "",
            "payload": {
                "firstName": lead.recipient_first_name,
                "lastName": lead.recipient_last_name,
                "companyName": lead.recipient_company,
                "website": lead.sender_company_website or "",
                "Subject": email_content.get('Subject', ''),
                "EmailBody": email_content.get('Email_Body', ''),
                "FollowUp": email_content.get('Follow_up', ''),
                "recipientRole": lead.recipient_role
            },
            "skip_if_in_workspace": True,
            "skip_if_in_campaign": True,
            "verify_leads_on_import": True
        }

        try:
            # Log the payload being sent
            self.logger.debug(f"Sending payload to {url}: {json.dumps(payload, indent=2)}")

            # Make the POST request to add the lead
            response = requests.post(url, headers=self.headers, json=payload)

            # Log the response details
            self.logger.debug(f"Response status code: {response.status_code}")
            self.logger.debug(f"Response text: {response.text}")

            # Check for success
            if response.status_code == 200:
                response_data = response.json()
                self.logger.success(f"Successfully added lead to campaign")
                return True
            else:
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('message', 'Unknown error')
                        self.logger.error(f"API Error: {error_msg}")
                    except ValueError:
                        self.logger.error(f"Error response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                    self.logger.error(f"API Error: {error_msg}")
                    self.logger.debug(f"Full error response: {json.dumps(error_data, indent=2)}")
                except ValueError:
                    self.logger.error(f"Error adding lead to campaign. Response text: {e.response.text}")
            else:
                self.logger.error(f"Request exception occurred: {str(e)}")
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error occurred while adding lead to campaign: {str(e)}")
            return False


class LeadProcessor:
    def __init__(self, api_keys: Dict[str, str]):
        self.logger = DebugLogger("LeadProcessor")

        airtable_key = api_keys.get('airtable_api_key')
        perplexity_key = api_keys.get('perplexity_api_key')
        openai_key = api_keys.get('openai_api_key')
        instantly_key = api_keys.get('instantly_api_key')
        base_id = api_keys.get('airtable_base_id')

        if not all([airtable_key, perplexity_key, openai_key, instantly_key, base_id]):
            raise ValueError("Missing required API keys")

        # Initialize components with retry handler
        self.logger.step("Initializing components...")
        self.retry_handler = RetryHandler()
        self.airtable = AirtableManager(airtable_key, base_id)
        self.perplexity = PerplexityEnricher(perplexity_key)
        self.email_gen = EmailGenerator(openai_key)
        self.instantly = InstantlyManager(instantly_key)
        self.logger.success("All components initialized")

    def create_destination_record(self, table_name: str, data: Dict) -> Optional[str]:
        """Creates a record in the destination table"""
        return self.retry_handler.retry_operation(
            self.airtable.create_record,
            table_name,
            data
        )

    def process_single_lead(self, lead_record: Dict):
        # Extract lead data
        lead = LeadData(
            unique_id=lead_record['id'],
            recipient_first_name=lead_record['fields'].get('recipient_first_name', ''),
            recipient_last_name=lead_record['fields'].get('recipient_last_name', ''),
            recipient_role=lead_record['fields'].get('recipient_role', ''),
            recipient_company=lead_record['fields'].get('recipient_company', ''),
            recipient_email=lead_record['fields'].get('recipient_email', ''),
            recipient_bio=lead_record['fields'].get('recipient_bio', ''),
            employment_summary=lead_record['fields'].get('employment_summary', ''),
            associated_client_id=lead_record['fields'].get('associated_client_id', ''),
            outreach_table=lead_record['fields'].get('outreach_table', ''),
            sender_name=lead_record['fields'].get('sender_name', ''),
            sender_title=lead_record['fields'].get('sender_title', ''),
            sender_company=lead_record['fields'].get('sender_company', ''),
            sender_email=lead_record['fields'].get('sender_email', ''),
            sender_company_website=lead_record['fields'].get('sender_company_website', ''),
            key_benefits=lead_record['fields'].get('key_benefits', ''),
            unique_features=lead_record['fields'].get('unique_features', ''),
            impact_metrics=lead_record['fields'].get('impact_metrics', ''),
            cta_options=lead_record['fields'].get('cta_options', ''),
            color_scheme=lead_record['fields'].get('color_scheme', ''),
            font_style=lead_record['fields'].get('font_style', '')
        )

        try:
            client_data = self.retry_handler.retry_operation(
                self.airtable.get_client_details,
                lead.associated_client_id
            )

            if not client_data:
                self.logger.warning(f"No client data found for {lead.associated_client_id}")
                return

            # Step 2: Enrich lead data with retry
            enriched_data = self.retry_handler.retry_operation(
                self.perplexity.enrich_lead,
                lead
            )

            # Step 3: Generate email content with retry
            email_content = self.retry_handler.retry_operation(
                self.email_gen.generate_content,
                lead,
                client_data['fields'],
                enriched_data
            )

            if not email_content:
                self.logger.error("Failed to generate email content")
                return

            # Step 4: Update original record
            update_fields = {
                'subject': email_content.get('Subject', ''),
                'email': email_content.get('Email_Body', ''),
                'follow_up': email_content.get('Follow_up', '')
            }

            update_success = self.retry_handler.retry_operation(
                self.airtable.update_record,
                'outreach_berkleys',
                lead.unique_id,
                update_fields
            )

            if not update_success:
                self.logger.error("Failed to update original record")
                return

            # Step 5: Create record in destination outreach table
            if lead.outreach_table:
                destination_record = self.retry_handler.retry_operation(
                    self.create_destination_record,
                    lead.outreach_table,
                    {
                        'subject': email_content.get('Subject', ''),
                        'email': email_content.get('Email_Body', ''),
                        'follow_up': email_content.get('Follow_up', ''),
                        'recipient_first_name': lead.recipient_first_name,
                        'recipient_last_name': lead.recipient_last_name,
                        'recipient_email': lead.recipient_email,
                        'recipient_company': lead.recipient_company,
                        'recipient_role': lead.recipient_role,
                        'associated_client_id': lead.associated_client_id
                    }
                )

                if not destination_record:
                    self.logger.error(f"Failed to create record in {lead.outreach_table}")
                    return

            # Step 6: Add to Instantly campaign
            campaign_success = self.retry_handler.retry_operation(
                self.instantly.add_to_campaign,
                "22795e87-2a6f-49be-b007-6f7f21840b05",  # Your correct campaign ID
                lead,
                email_content
            )

            if campaign_success:
                self.logger.success("Successfully processed lead")
            else:
                self.logger.error("Failed to add lead to Instantly campaign")

        except Exception as e:
            self.logger.error(f"Error processing lead: {str(e)}")

    def process_leads(self):
        """Process all new leads"""
        self.logger.step("Starting lead processing")

        try:
            # Get new leads with retry
            leads = self.retry_handler.retry_operation(
                self.airtable.get_new_leads,
                'outreach_berkleys'
            )

            for lead in leads:
                try:
                    self.process_single_lead(lead)
                except Exception as e:
                    self.logger.error(f"Error processing lead {lead.get('id', 'unknown')}: {e}")
                    continue

            self.logger.success(f"Completed processing {len(leads)} leads")

        except Exception as e:
            self.logger.error(f"Fatal error in lead processing: {e}")

def main():
    logger = DebugLogger("Main")

    # Load configuration
    config = {
        'airtable_api_key': os.getenv('AIRTABLE_API_KEY'),
        'perplexity_api_key': os.getenv('PERPLEXITY_API_KEY'),
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'instantly_api_key': os.getenv('INSTANTLY_API_KEY'),
        'airtable_base_id': 'app5s8zl7DsUaDmtx'
    }

    # Validate configuration
    missing_keys = [k for k, v in config.items() if not v]
    if missing_keys:
        logger.error(f"Missing configuration keys: {', '.join(missing_keys)}")
        return

    try:
        processor = LeadProcessor(config)
        processor.process_leads()
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()