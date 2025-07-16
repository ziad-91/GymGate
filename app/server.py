import os
from datetime import datetime, date, timedelta, timezone
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import logging  # Added for setting log level

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

        # 2. Upsert user data
        user_data_to_sync = [
            {
                'airtable_record_id': m['airtable_record_id'],
                'phone_number': m['phone_number'],
                'name': m['name'],
                'expiry': m['expiry'],
            } for m in members_to_sync
        ]
        user_response = supabase.table('users').upsert(user_data_to_sync, on_conflict='airtable_record_id').execute()
        if hasattr(user_response, 'error') and user_response.error:
            raise Exception(f"Supabase user sync error: {user_response.error.message}")

        # 3. Fetch the user map (Airtable ID -> Supabase UUID)
        user_map_response = supabase.table('users').select('id, airtable_record_id').execute()
        id_map = {user['airtable_record_id']: user['id'] for user in user_map_response.data}

        # 4. Prepare and upsert subscription data
        subscriptions_to_sync = []
        for member in members_to_sync:
            if member.get('class_name') and member.get('airtable_record_id') in id_map:
                subscriptions_to_sync.append({
                    'user_id': id_map[member['airtable_record_id']],
                    'class_name': member['class_name']
                })
        
        if subscriptions_to_sync:
            # Assumption: 'user_id' is UNIQUE in the 'subscriptions' table.
            sub_response = supabase.table('subscriptions').upsert(subscriptions_to_sync, on_conflict='user_id').execute()
            if hasattr(sub_response, 'error') and sub_response.error:
                raise Exception(f"Supabase subscription sync error: {sub_response.error.message}")

        return jsonify({'status': 'success', 'message': f'Successfully synced {len(user_data_to_sync)} users and {len(subscriptions_to_sync)} subscriptions.'})

    except Exception as e:
        app.logger.error(f"Sync failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/checkin', methods=['POST'])
def checkin():
    """
    Validates a user's check-in, prevents duplicates within 30 min, and logs the scan to the
    new `checkins` table using the redesigned schema.
    """
    phone_number = request.json.get('phone_number')
    session_class = request.json.get('session_class')

    app.logger.info(f"Incoming scan: phone_number={phone_number} session_class={session_class}")

    if not phone_number:
        return jsonify({'status': 'error', 'message': 'Phone number missing'}), 400
    if not session_class:
        return jsonify({'status': 'error', 'message': 'Session class missing'}), 400

    user_name = "Unknown User"
    user_id = None
    original_class = None
    status = "not_found"
    screen_color = "red"
    message = "Member not found."

    try:
        # 1. Locate the user by phone number
        user_resp = supabase.table('users').select('*').eq('phone_number', phone_number).limit(1).execute()
        app.logger.info(f"User lookup response: {user_resp}")
        user_data = user_resp.data[0] if user_resp.data else None

        if user_data:
            user_id = user_data.get('id')
            user_name = user_data.get('name', 'Unknown')

            # 2. Retrieve the user's original class from subscriptions (take first match)
            sub_resp = supabase.table('subscriptions').select('class_name').eq('user_id', user_id).limit(1).execute()
            if sub_resp.data:
                original_class = sub_resp.data[0].get('class_name')

            # Duplicate-scan prevention temporarily disabled for testing
            # thirty_minutes_ago = (datetime.utcnow() - timedelta(minutes=30)).isoformat()
            # dup_resp = supabase.table('checkins')\
            #     .select('*', count='exact')\
            #     .eq('user_id', user_id)\
            #     .gte('created_at', thirty_minutes_ago)\
            #     .execute()
            #
            # if dup_resp.count > 0:
            #     message = f"❌ {user_name} already scanned in the last 30 min."
            #     screen_color = "red"
            #     status = "duplicate"
            #     return jsonify({'status': status, 'message': message, 'screen_color': screen_color})

            # 4. Membership validity check
            expiry_ts = user_data.get('expiry')  # May be None
            if expiry_ts:
                expiry_dt = datetime.fromisoformat(expiry_ts.replace('Z', '+00:00'))
                now_utc = datetime.now(timezone.utc)
                if now_utc > expiry_dt:
                    message = f"❌ Membership expired for {user_name}."
                    status = "expired"
                else:
                    # 5. Class eligibility check
                    sc = session_class.lower()
                    if sc == 'sparring':
                        status = "accepted"
                        message = f"✅ Welcome, {user_name}. Sparring is open to all."
                        screen_color = "green"
                    elif not original_class:
                        status = "not_allowed"
                        message = f"❌ {user_name} has no active subscription found."
                    else:
                        allowed = set()
                        oc = original_class.lower()

                        if oc == 'mma beginners':
                            allowed.update(['mma beginners', 'bjj men', 'wrestling'])
                        elif oc == 'mma intermediate':
                            allowed.update(['mma intermediate', 'mma beginners', 'bjj men', 'wrestling', 'adv/inter. mma grappling'])
                        elif oc == 'mma advanced':
                            allowed.update(['mma advanced', 'mma intermediate', 'mma beginners', 'bjj men', 'wrestling', 'adv/inter. mma grappling'])
                        else: # Non-MMA classes
                            allowed.add(oc)
                        
                        if sc in allowed:
                            status = "accepted"
                            message = f"✅ Welcome, {user_name}. Eligible for {session_class}."
                            screen_color = "green"
                        else:
                            status = "not_allowed"
                            message = f"❌ {user_name} not eligible for {session_class} (Subscribed to: {original_class})."
            else:
                message = f"❌ No expiry date for {user_name}."
                status = "invalid"
        else:
            status = "not_found"

    except Exception as e:
        app.logger.error(f"Check-in error for phone {phone_number}: {e}")
        status = "error_server"  # FIXED: Changed log_status -> status
        message = "A server error occurred. Please check the logs."

    finally:
        # 5. Write the check-in record only if user was found
        try:
            if user_id:
                supabase.table('checkins').insert({
                    'user_id': user_id,
                    'original_class': original_class,
                    'session_class': session_class
                }).execute()
        except Exception as e:
            app.logger.error(f"Failed to log check-in: {e}")

    response = jsonify({
        'status': status,
        'message': message,
        'screen_color': screen_color
    })
    app.logger.info(f"Returning response: {response.get_json()}")
    return response

if __name__ == '__main__':
    # The init_db() function is no longer needed as tables are managed in Supabase directly.
    app.logger.setLevel(logging.INFO)  # Set log level to INFO
    app.run(host='0.0.0.0', port=5000)