import os
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client

# Import the new data fetching function
from airtable_sync import fetch_airtable_data

# --- App Initialization ---
app = Flask(__name__, static_folder='static')
CORS(app)

# --- Environment and Supabase Setup ---
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SYNC_PASSWORD = os.getenv('SYNC_PASSWORD')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Check for missing environment variables
if not all([SYNC_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
    raise RuntimeError("Missing required environment variables. Please check your .env file.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/sync_airtable', methods=['POST'])
def sync_airtable():
    """
    Fetches data from Airtable and upserts it into the Supabase 'members' table.
    This endpoint is password-protected.
    """
    password = request.json.get('password')
    if password != SYNC_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    try:
        # 1. Fetch and transform data from Airtable
        members_to_sync = fetch_airtable_data()
        if not members_to_sync:
            return jsonify({'status': 'success', 'message': 'No members found in Airtable to sync.'})

        # 2. Upsert data into Supabase
        # 'id' is the conflict resolution column, ensuring stable updates.
        response = supabase.table('members').upsert(members_to_sync, on_conflict='id').execute()
        
        # Check for errors in the response
        if hasattr(response, 'error') and response.error:
            raise Exception(f"Supabase error: {response.error.message}")

        return jsonify({'status': 'success', 'message': f'Successfully synced {len(members_to_sync)} members.'})

    except Exception as e:
        app.logger.error(f"Sync failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/checkin', methods=['POST'])
def checkin():
    """
    Validates a member's check-in against the Supabase DB and logs the attempt.
    """
    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({'status': 'error', 'message': 'Phone number missing'}), 400

    member_name = "Unknown Member"
    log_status = "not_found"
    message = "Member not found."
    screen_color = "red"
    member_id_to_log = None

    try:
        # 1. Find the member in Supabase by their phone number
        response = supabase.table('members').select('*').eq('phone_number', phone_number).limit(1).execute()
        member_data = response.data[0] if response.data else None

        if member_data:
            member_id_to_log = member_data.get('id') # Get the member's primary key
            member_name = member_data.get('name', 'Unknown')
            expiry_date_str = member_data.get('membership_expiry_date')

            if expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                if date.today() <= expiry_date:
                    message = f"✅ Welcome, {member_name} — Membership active."
                    screen_color = "green"
                    log_status = "active"
                else:
                    message = f"❌ Membership expired for {member_name}. Please renew."
                    screen_color = "red"
                    log_status = "expired"
            else:
                message = f"No expiry date found for {member_name}."
                screen_color = "red"
                log_status = "error_no_date"
        else:
            log_status = "not_found"

    except Exception as e:
        app.logger.error(f"Check-in error for phone {phone_number}: {e}")
        log_status = "error_server"
        message = "A server error occurred. Please check the logs."

    finally:
        # 2. Log the check-in attempt, linking it to the member if found
        try:
            supabase.table('checkins').insert({
                'phone_number_scanned': phone_number,
                'member_name': member_name,
                'status': log_status,
                'member_id': member_id_to_log # This creates the foreign key link
            }).execute()
        except Exception as e:
            app.logger.error(f"Failed to log check-in: {e}")

    return jsonify({
        'status': log_status,
        'message': message,
        'screen_color': screen_color
    })

if __name__ == '__main__':
    # The init_db() function is no longer needed as tables are managed in Supabase directly.
    app.run(host='0.0.0.0', port=5000)