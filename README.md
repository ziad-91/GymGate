# TKO Martial Arts - QR Code Membership Scanner

This web application provides a QR code-based check-in system for the TKO Martial Arts gym. It scans a member's QR code, verifies their membership status against an Airtable database, and displays a confirmation message.

---

## Features

- **QR Code Scanning**: Uses the device's camera to scan member QR codes.
- **Airtable Integration**: Syncs member data directly from an Airtable base.
- **Local Database Cache**: Stores member data in a local SQLite database for fast lookups.
---

## Setup and Configuration

### 1. Environment Variables (`.env`)

Create a file named `.env` in the project root. Copy the template below and fill it with your actual credentials. **This file must not be committed to Git.**

```sh
# .env file

# Airtable Credentials (for data syncing)
AIRTABLE_TOKEN=patYOUR_AIRTABLE_PERSONAL_ACCESS_TOKEN
AIRTABLE_BASE_ID=appYOUR_AIRTABLE_BASE_ID
AIRTABLE_TABLE_NAME=Your Airtable Table Name

# Supabase Credentials (the live database)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# Sync Password (to protect the sync button)
SYNC_PASSWORD=create-a-strong-password
```

### 2. Supabase Database Setup

Before running the app, you must create the necessary tables in your Supabase project.

1.  Navigate to the **SQL Editor** in your Supabase dashboard.
2.  Run the following SQL commands one by one:

**Create the `members` table:**
```sql
-- Drop the old table first if it exists, to start fresh.
DROP TABLE IF EXISTS public.members CASCADE;

-- Create the new members table with 'id' as the primary key
CREATE TABLE public.members (
  id INT PRIMARY KEY NOT NULL, -- The Autonumber from Airtable
  phone_number TEXT UNIQUE,    -- Phone number is still unique, but not the PK
  name TEXT NOT NULL,
  status TEXT,
  membership_expiry_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.members IS 'Stores member data synced from Airtable, using Airtable Autonumber as ID.';
```

**Create the `checkins` table:**
```sql
-- Drop the old table first if it exists
DROP TABLE IF EXISTS public.checkins;

-- Create the new checkins table with a foreign key to members.id
CREATE TABLE public.checkins (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  phone_number_scanned TEXT,
  member_name TEXT,
  status TEXT NOT NULL,
  member_id INT REFERENCES public.members(id) ON DELETE SET NULL
);

COMMENT ON TABLE public.checkins IS 'Logs every QR code scan attempt, linked to a member ID.';
```

### 3. Install Dependencies

Install all required Python packages:
```sh
pip install -r requirements.txt
```

---

## Running Locally

1.  **Start the Server**:
    ```sh
    python app/server.py
    ```
2.  **Access the App**: Open your browser to `http://127.0.0.1:5000`.
3.  **Sync the Database**: Click the **"Sync with Airtable"** button and enter your `SYNC_PASSWORD`. This will pull data from Airtable into your Supabase database.

---

## Deployment on Render

This application is configured for easy deployment on [Render](https://render.com/).

1.  **Push to GitHub**: Make sure all your latest code changes are pushed to your GitHub repository.
2.  **Create Blueprint Service**: On your Render dashboard, click **New +** > **Blueprint** and connect your GitHub repo. Render will automatically use the `render.yaml` file.
3.  **Add Environment Variables**: In your Render service's **Environment** tab, create an "Environment Group" or add the following secrets individually. These must match your `.env` file.
    - `AIRTABLE_TOKEN`
    - `AIRTABLE_BASE_ID`
    - `AIRTABLE_TABLE_NAME`
    - `SUPABASE_URL`
    - `SUPABASE_SERVICE_KEY`
    - `SYNC_PASSWORD`
4.  **Deploy**: Click **Create New Blueprint Service**. Render will build and deploy your app. Once live, you can access it from anywhere using the public URL provided.
