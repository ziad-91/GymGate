# TKO Martial Arts - QR Code Membership Scanner

This web application provides a QR code-based check-in system for the TKO Martial Arts gym. It scans a member's QR code, verifies their membership status against an Airtable database, and displays a confirmation message.

---

## Features

- **QR Code Scanning**: Uses the device's camera to scan member QR codes.
- **Airtable Integration**: Syncs member data directly from an Airtable base.
- **Local Database Cache**: Stores member data in a local SQLite database for fast lookups.
- **Password-Protected Sync**: A "Sync with Airtable" button allows an admin to update the local database with the latest member info.

---

## How It Works

1.  **QR Codes**: Each member has a QR code that encodes their unique phone number.
2.  **Airtable**: The gym owner maintains a list of all members in an Airtable base. This is the single source of truth for membership status and expiry dates.
3.  **Syncing**: An admin can press the "Sync with Airtable" button on the web app. This fetches all member records from Airtable and saves them to a local `members.db` SQLite file.
4.  **Scanning**: When a QR code is scanned, the app reads the phone number and looks it up in the local `members.db` to check the membership expiry date.

---

## Setup and Installation

Follow these steps to run the application on your local machine.

### 1. Prerequisites

- Python 3.x
- `pip` (Python package installer)

### 2. Configure Environment Variables

Create a file named `.env` in the project's root directory. This file will store your secret credentials. Add the following content to it, replacing the placeholder values with your own:

```
# .env file

# Get this from your Airtable account settings (https://airtable.com/create/tokens)
# Ensure it has `data.records:read` scope and access to your TKO base.
AIRTABLE_TOKEN=patYOUR_AIRTABLE_PERSONAL_ACCESS_TOKEN

# Find this on your Airtable API documentation page for your base.
AIRTABLE_BASE_ID=appjDTBGG5XjjmwiW

# The exact name of the table containing your members.
AIRTABLE_TABLE_NAME=TKO Members

# A password to protect the database sync functionality.
SYNC_PASSWORD=changeme123
```

### 3. Install Dependencies

Open your terminal in the project root folder and run the following command to install the required Python packages:

```sh
pip install -r requirements.txt
```

---

## Running the Application

### 1. Launch the Server

To start the web application, run the following command from the project's root directory:

```sh
python app/server.py
```

The server will start, and you will see output indicating it is running on `http://127.0.0.1:5000`.

### 2. Access the App

Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 3. Sync the Database

Before you can scan members, you must sync the database with Airtable:
1.  Click the **"Sync with Airtable"** button.
2.  When prompted, enter the `SYNC_PASSWORD` you set in your `.env` file.
3.  A message will confirm the number of members synced.

Your application is now ready to scan QR codes.
