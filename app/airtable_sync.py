import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME.replace(' ', '%20')}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_airtable_data():
    """Fetches all member records from Airtable and prepares them for Supabase."""
    all_records = []
    offset = None

    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(API_URL, headers=HEADERS, params=params)
        response.raise_for_status()  # Raises an error for bad responses (4xx or 5xx)
        data = response.json()
        
        all_records.extend(data.get('records', []))
        
        offset = data.get('offset')
        if not offset:
            break

    # Transform records for Supabase upsert
    members_for_supabase = []
    for record in all_records:
        fields = record.get('fields', {})
        # The Autonumber ID from Airtable is now the primary key
        member_id = fields.get('id')
        phone = fields.get('Phone')

        # Skip records without an ID
        if member_id is None:
            continue

        # Ensure expiry date is in a valid format or null
        expiry_date = fields.get('Expiry')
        if expiry_date:
            try:
                # Validate and format the date
                datetime.strptime(expiry_date, '%Y-%m-%d')
            except ValueError:
                expiry_date = None # Set to null if format is invalid
        
        members_for_supabase.append({
            "id": int(member_id),
            "phone_number": str(phone).strip() if phone else None,
            "name": fields.get('Name', 'Unknown'),
            "status": fields.get('Status', 'Unknown'),
            "membership_expiry_date": expiry_date,
            "updated_at": datetime.utcnow().isoformat() # Track when the sync happened
        })

    return members_for_supabase
