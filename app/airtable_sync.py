import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

# Check for missing Airtable environment variables
if not all([AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME]):
    raise RuntimeError("Missing Airtable environment variables (TOKEN, BASE_ID, TABLE_NAME). Please check your .env file.")

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

        # Skip records without an ID
        if member_id is None:
            continue

        # Ensure expiry date is in a valid format or null
        expiry_date = None
        expiry_date_str = fields.get('Expiry') # Match Airtable field name
        if expiry_date_str:
            try:
                # Assuming date format is like '2023-10-25'
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date().isoformat()
            except (ValueError, TypeError):
                expiry_date = None

        phone_number = str(fields.get('Phone')).strip() if fields.get('Phone') else None

        # Only add members if they have a phone number, as it's required for the QR scanner.
        if phone_number:
            # Handle class name, which might be a list or a string
            raw_class = fields.get('Classes')
            class_name = None
            if isinstance(raw_class, list) and raw_class:
                class_name = raw_class[0].strip()
            elif isinstance(raw_class, str):
                class_name = raw_class.strip()

            # This dictionary's keys MUST match the Supabase column names exactly.
            members_for_supabase.append({
                'airtable_record_id': record['id'],
                'phone_number': phone_number,
                'name': fields.get('Name', 'Unknown'),
                'expiry': expiry_date,
                'class_name': class_name
            })

    return members_for_supabase
