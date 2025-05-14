import csv
import requests
import smtplib
from email.message import EmailMessage

# Airtable Configuration
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'leads_guideline'
CSV_FILE = 'leads_guideline.csv'

# Gmail Configuration
EMAIL_ADDRESS = 'shibla@taippa.com'
EMAIL_PASSWORD = 'rkecttakcyajughv'  # App password
TO_EMAIL = 'shiblashilu@gmail.com'

def fetch_airtable_data_and_create_csv():
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}
    
    records = []
    offset = None
    while True:
        params = {'offset': offset} if offset else {}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break

    if records:
        fieldnames = list(records[0]['fields'].keys())
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record['fields'])
        print("CSV created successfully.")
    else:
        print("No records found in Airtable.")

def send_email_with_csv():
    msg = EmailMessage()
    msg['Subject'] = 'Leads Guideline CSV'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content('Attached is the leads_guideline CSV file.')

    with open(CSV_FILE, 'rb') as f:
        file_data = f.read()
        file_name = f.name
        msg.add_attachment(file_data, maintype='text', subtype='csv', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully.")

if __name__ == '__main__':
    fetch_airtable_data_and_create_csv()
    send_email_with_csv()
