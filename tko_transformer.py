import pandas as pd
import csv

csv_path = r"C:\\Users\\zmars\\OneDrive\Desktop\\Clients\\TKO Martial Arts\\TKO Members - TKO Members.csv"
df = pd.read_csv(csv_path)

# === STEP 2: Extract and rename relevant columns ===
class_table = df[['ID', 'Classes']].copy()
print( df[['ID', 'Classes']])
class_table.columns = ['user_id', 'class_name']

with open('output.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(class_table)
print ("done")
# === STEP 3 (optional): Upload to Supabase ===
# Supabase config
# SUPABASE_URL = "https://your-project-id.supabase.co"
# SUPABASE_API_KEY = "your-secret-api-key"
# SUPABASE_TABLE = "subscriptions"

# Headers for Supabase
# headers = {
#     "apikey": SUPABASE_API_KEY,
#     "Authorization": f"Bearer {SUPABASE_API_KEY}",
#     "Content-Type": "application/json",
#     "Prefer": "return=minimal"
# }
