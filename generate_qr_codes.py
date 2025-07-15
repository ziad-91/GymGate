import csv
import os
import qrcode

CSV_FILE = "TKO Members.csv"
OUTPUT_DIR = "qr_codes"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def try_open_csv(encodings):
    for enc in encodings:
        try:
            with open(CSV_FILE, newline='', encoding=enc) as csvfile:
                return list(csv.reader(csvfile))
        except Exception as e:
            print(f"Failed to read with encoding {enc}: {e}")
    raise Exception("Could not read CSV with any encoding.")

rows = try_open_csv(['utf-8-sig', 'utf-8', 'latin1'])

for row in rows:
    try:
        if len(row) < 2:
            continue
        name = row[0].strip().replace(" ", "_").replace("/", "_")
        phone = str(row[1]).strip()
        if not phone or not name:
            continue
        filename = f"{name}_{phone}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            print(f"Skipped existing QR for {name}: {filepath}")
            continue
        img = qrcode.make(phone)
        img.save(filepath)
        print(f"Saved QR for {name}: {filepath}")
    except Exception as e:
        print(f"Skipped row due to error: {e}")