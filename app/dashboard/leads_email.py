from flask import Flask
import csv
import requests
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'leads_guideline'
CSV_FILE = 'leads_guideline.csv'

# Gmail Configuration
EMAIL_ADDRESS = 'shibla@taippa.com'
EMAIL_PASSWORD = 'rkecttakcyajughv'
TO_EMAIL = 'shiblashilu@gmail.com'
CC_EMAILS = ['shilusaifshilu@gmail.com', 'sravan@taippa.com'] 
def generate_csv_and_send_email():
    # Fetch data from Airtable
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}

    records = []
    offset = None
    while True:
        params = {'offset': offset} if offset else {}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Failed to fetch Airtable data: {response.text}", 500
        data = response.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break

    if not records:
        return "No records found.", 404

    # Write data to CSV
    fieldnames = list(records[0]['fields'].keys())
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record['fields'])

    # Create and send email with attachment
    msg = EmailMessage()
    msg['Subject'] = 'Leads Guideline CSV'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Cc'] = ', '.join(CC_EMAILS)
    msg.set_content('Attached is the leads_guideline CSV file.')

    with open(CSV_FILE, 'rb') as f:
        msg.add_attachment(f.read(), maintype='text', subtype='csv', filename=f.name)

    recipients = [TO_EMAIL] + CC_EMAILS

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg, to_addrs=recipients)

    return "CSV created and email sent successfully."


