import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME.replace(' ', '%20')}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

# Fetch all records from Airtable (pagination supported)
def fetch_all_members():
    members = []
    offset = None
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        resp = requests.get(API_URL, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        for record in data['records']:
            fields = record.get('fields', {})
            members.append({
                'name': fields.get('Name', ''),
                'phone': str(fields.get('Phone', '')),
                'classes': fields.get('Classes', ''),
                'status': fields.get('Status', ''),
                'last_renewed': fields.get('Last Renewed', ''),
                'expiry': fields.get('Expiry', '')
            })
        if 'offset' in data:
            offset = data['offset']
        else:
            break
    return members
