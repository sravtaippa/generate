"""
Email Generation System - Complete Implementation
Matches all Make.com scenario functionality including multiple table management,
robust error handling, and complete workflow alignment.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from time import sleep
import requests
import openai
import colorama
from colorama import Fore, Style

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
            'maxRecords': 15,  # Matching Make.com scenario limit
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

        You're tasked with producing the best cold outreach email template for a campaign.
        What should the structure and format be for a {business_type} business?
        Use industry best practices to maximize open rates, click-through rates and conversion rates.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
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
            prompt = f"""You're writing a cold outreach email.

Return ONLY a JSON object with this exact structure:
{{
    "Subject": "The email subject line",
    "Email_Body": "The main email body",
    "Follow_up": "The follow-up email content"
}}

Recipient Information:
- Name: {lead.recipient_first_name} {lead.recipient_last_name}
- Role: {lead.recipient_role}
- Company: {lead.recipient_company}
- Bio: {lead.recipient_bio}

Client Information:
- Benefits: {client_data.get('solution_benefits', '')}
- Features: {client_data.get('unique_features', '')}
- Domain: {client_data.get('domain', '')}
- Business Type: {client_data.get('business_type', '')}

Additional Context:
{enriched_data}

Follow this template structure:
{template}

The email should:
1. Start with a personalized ice breaker
2. Show clear relevance to the recipient
3. Address specific pain points
4. Use industry-specific language
5. Have a clear call to action
6. Include proper signature with all sender details

Format the email with {lead.font_style} font style and {lead.color_scheme} color scheme for visual appeal.
Sign off with:
{lead.sender_name}
{lead.sender_title}
{lead.sender_company}
{lead.sender_company_website}"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()
            self.logger.debug(f"Raw response: {content}")

            try:
                email_content = json.loads(content)
                self.logger.success("Generated email content")
                return email_content
            except json.JSONDecodeError as je:
                self.logger.error(f"JSON parsing error: {je}")
                return {}

        except Exception as e:
            self.logger.error(f"Error generating email: {str(e)}")
            return {}



import requests
import json
from typing import Dict

import requests
import json
from typing import Dict

import requests
import json
from typing import Dict

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
        url = f"{self.base_url}/leads"  # Corrected endpoint

        # Prepare the payload for the request
        lead_data = {
            "email": lead.recipient_email,
            "firstName": lead.recipient_first_name or "",
            "lastName": lead.recipient_last_name or "",
            "companyName": lead.recipient_company or "",
            "variables": {
                "Subject": email_content.get('Subject', ''),
                "EmailBody": email_content.get('Email_Body', ''),
                "FollowUp": email_content.get('Follow_up', ''),
                "uniqueId": lead.unique_id or ''
            }
        }

        payload = {
            "campaignId": campaign_id,
            "leads": [lead_data]
        }

        try:
            # Log the payload being sent
            self.logger.debug(f"Sending payload to {url}: {json.dumps(payload, indent=2)}")

            # Make the POST request to add the lead
            response = requests.post(url, headers=self.headers, json=payload)

            # Log the response details for debugging
            self.logger.debug(f"Response status code: {response.status_code}")
            self.logger.debug(f"Response text: {response.text}")

            # Check for HTTP errors
            response.raise_for_status()

            # Parse the JSON response
            response_data = response.json()
            if response_data.get('success', False):
                self.logger.success("Successfully added lead to campaign")
                return True
            else:
                error_msg = response_data.get('message', 'Unknown error')
                self.logger.error(f"Failed to add lead: {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            if e.response is not None:
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
            # Catch any unexpected exceptions and log them
            self.logger.error(f"Unexpected error occurred while adding lead to campaign: {str(e)}")
            return False



class LeadProcessor:
    def __init__(self, api_keys: Dict[str, str]):
        self.logger = DebugLogger("LeadProcessor")

        # Extract required API keys
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
        """Process a single lead with full Make.com scenario functionality"""
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
            # Step 1: Get client data with retry
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
                "22795e87-2a6f-49be-b007-6f7f21840b05",  # Campaign ID from Make.com
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