import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from airtable_sync import fetch_all_members

app = Flask(__name__, static_folder='static')
CORS(app)
DATABASE = 'members.db'
LOG_TABLE = 'check_ins'

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
SYNC_PASSWORD = os.getenv('SYNC_PASSWORD', 'changeme123')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Members table (synced from Airtable)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                phone_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                membership_expiry_date TEXT NOT NULL
            )
        ''')
        # Check-ins log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS check_ins (
                timestamp TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                member_name TEXT,
                status TEXT NOT NULL
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkin', methods=['POST'])
def checkin():
    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({'status': 'error', 'message': 'Phone number missing'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    member = cursor.execute('SELECT * FROM members WHERE phone_number = ?', (phone_number,)).fetchone()

    current_time = datetime.now().isoformat()
    log_status = "unknown"
    member_name = "Unknown Member"
    message = "Member not found."
    screen_color = "red"

    if member:
        member_name = member['name']
        expiry_date_str = member['membership_expiry_date']
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if today <= expiry_date:
                message = f"✅ Welcome, {member_name} — Membership active."
                screen_color = "green"
                log_status = "active"
            else:
                message = f"❌ Membership expired for {member_name}. Please renew."
                screen_color = "red"
                log_status = "expired"
        except ValueError:
            message = f"Error: Invalid expiry date format for {member_name}."
            screen_color = "red"
            log_status = "error_date_format"
    else:
        log_status = "not_found"

    # Log the check-in
    cursor.execute('''
        INSERT INTO check_ins (timestamp, phone_number, member_name, status)
        VALUES (?, ?, ?, ?)
    ''', (current_time, phone_number, member_name, log_status))
    conn.commit()
    conn.close()

    return jsonify({
        'status': log_status,
        'message': message,
        'screen_color': screen_color
    })

@app.route('/sync_airtable', methods=['POST'])
def sync_airtable():
    password = request.json.get('password')
    if password != SYNC_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    try:
        members = fetch_all_members()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM members')
            for m in members:
                # Defensive: fallback to empty string if missing
                cursor.execute('''
                    INSERT OR REPLACE INTO members (phone_number, name, membership_expiry_date)
                    VALUES (?, ?, ?)
                ''', (
                    m.get('phone', ''),
                    m.get('name', ''),
                    m.get('expiry', '')
                ))
            conn.commit()
        return jsonify({'status': 'success', 'message': f'Synced {len(members)} members from Airtable.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)