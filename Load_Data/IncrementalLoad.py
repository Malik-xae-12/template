import re
from datetime import datetime, timedelta
import os
import pdfplumber
import pyodbc

# ---------- CONFIG ----------
SQL_SERVER = 
SQL_DATABASE = 
SQL_USERNAME = 
SQL_PASSWORD = 
SQL_DRIVER = '{ODBC Driver 17 for SQL Server}'
BATCH_SIZE = 1000
BASE_DIR = r"E:\TC_BC\Appointments"   # <---- base directory
# ---------- DB CONNECTION ----------
def get_connection():
    connection_string = f'DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}'
    return pyodbc.connect(connection_string)

def initialize_db():
    """Ensure appointments table exists and clean old records."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Create appointments table if not exists
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'appointments')
            CREATE TABLE appointments (
                urn NVARCHAR(50),
                care_provider NVARCHAR(255),
                location NVARCHAR(255),
                gender NVARCHAR(1),
                patient_name NVARCHAR(255),
                start_date NVARCHAR(10),
                end_date NVARCHAR(10),
                timestamp NVARCHAR(16),
                pdf_path NVARCHAR(255)
            )
        """)
        conn.commit()

        # Cleanup old records (older than 30 days by start_date)
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute("DELETE FROM appointments WHERE TRY_CONVERT(date, start_date, 120) < ?", cutoff_date)
        conn.commit()
        print(f"🗑️ Old records before {cutoff_date} removed from appointments table.")

        conn.close()
    except Exception as e:
        print(f"\033[91m❌ Error initializing DB: {e}\033[0m")

# ---------- PDF EXTRACTION ----------
def extract_text_with_pdfplumber(pdf_path):
    """Extract text from all pages of a PDF."""
    if not os.path.exists(pdf_path):
        print(f"\033[91m❌ PDF file not found: {pdf_path}\033[0m")
        return None

    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    all_text += f"\n--- Page {page_num} ---\n{text}"
                    print(f"\033[92m✅ Extracted page {page_num} from {pdf_path}\033[0m")
        return all_text
    except Exception as e:
        print(f"\033[91m❌ Error extracting PDF {pdf_path}: {e}\033[0m")
        return None

# ---------- PROCESS TEXT INTO DB ----------
def save_appointments_from_text(extracted_text, pdf_path):
    """Parse extracted text and save appointments into SQL Server DB (no txt file)."""
    if not extracted_text:
        print(f"\033[93m❌ No text to process for {pdf_path}\033[0m")
        return 0

    try:
        conn = get_connection()
        cursor = conn.cursor()
    except pyodbc.Error as e:
        print(f"\033[91m❌ Failed to connect to SQL Server: {e}\033[0m")
        return 0

    period_start = None
    period_end = None
    current_care_provider = None
    current_location = None

    appointments_processed = 0
    lines = extracted_text.splitlines()
    print(f"📝 Processing {len(lines)} lines of text from {pdf_path}...")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Period line
        if line.startswith("Period:") and period_start is None:
            match = re.search(r"Period:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", line)
            if match:
                try:
                    period_start = datetime.strptime(match.group(1), '%d/%m/%Y').date()
                    period_end = datetime.strptime(match.group(2), '%d/%m/%Y').date()
                    print(f"✅ Period set for {pdf_path}: {period_start} to {period_end}")
                except ValueError as e:
                    print(f"\033[93m⚠️ Error parsing period dates in {pdf_path}: {line}\nError: {e}\033[0m")
                    period_start = datetime.now().date()
                    period_end = period_start
            else:
                print(f"\033[93m⚠️ No valid date range found in {pdf_path}: {line}\033[0m")
                period_start = datetime.now().date()
                period_end = period_start
            continue

        # Care Provider
        if line.startswith("Care Provider:") or line.startswith("Care Provider/Resource:"):
            current_care_provider = line.replace("Care Provider:", "").replace("Care Provider/Resource:", "").strip()
            print(f"✅ Care Provider set for {pdf_path}: {current_care_provider}")
            continue

        # Location
        if line.startswith("Location:"):
            current_location = line.replace("Location:", "").strip()
            print(f"✅ Location set for {pdf_path}: {current_location}")
            continue

        # Appointment rows
        if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", line):
            period_start = period_start or datetime.now().date()
            period_end = period_end or period_start
            current_care_provider = current_care_provider or "Unknown Provider"
            current_location = current_location or "Unknown Location"

            try:
                parts = line.split()
                date_part = parts[0]
                time_part = parts[1]
                urn = parts[2][:-1]

                patient_name_parts = []
                gender = None
                for j in range(3, len(parts)):
                    if re.match(r'\d{10,}', parts[j]):
                        break
                    if parts[j].lower() in ['transferred', 'booked', 'new', 'patient', 'visit', 'follow', 'up', 'established']:
                        break
                    if parts[j] in ['M', 'F'] and gender is None:
                        gender = parts[j]
                    else:
                        patient_name_parts.append(parts[j])

                patient_name_raw = " ".join(patient_name_parts).strip()
                patient_name_parts = patient_name_raw.split()
                if patient_name_parts and len(patient_name_parts[-1]) == 1 and patient_name_parts[-1].isalpha():
                    patient_name = " ".join(patient_name_parts[:-1]).strip()
                else:
                    patient_name = patient_name_raw

                gender = gender or "U"
                timestamp = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")

                start_date_str = period_start.strftime('%Y-%m-%d')
                end_date_str = period_end.strftime('%Y-%m-%d')
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")

                try:
                    cursor.execute("""
                        INSERT INTO appointments (urn, care_provider, location, gender, patient_name, start_date, end_date, timestamp, pdf_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (urn, current_care_provider, current_location, gender, patient_name, start_date_str, end_date_str, timestamp_str, pdf_path))
                    conn.commit()
                    appointments_processed += 1
                    print(f"✅ Created: URN={urn}, Patient='{patient_name}', Gender={gender}, Date={timestamp}")
                except pyodbc.Error as db_error:
                    print(f"\033[91m❌ Database error creating URN={urn}: {db_error}\033[0m")
                    continue

            except Exception as e:
                print(f"\033[93m⚠️ Error processing line in {pdf_path}: {line}\nError: {e}\033[0m")
                continue

    conn.close()
    return appointments_processed

# ---------- PROCESS ALL PDFs ----------
def process_pdfs_in_directory(directory):
    """Process all PDFs in the directory and its subfolders."""
    total_processed = 0
    pdf_count = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                print(f"\n📄 Processing PDF: {pdf_path}")
                pdf_count += 1
                extracted_text = extract_text_with_pdfplumber(pdf_path)
                if extracted_text:
                    processed = save_appointments_from_text(extracted_text, pdf_path)
                    total_processed += processed
                else:
                    print(f"\033[93m⚠️ No text extracted from {pdf_path}\033[0m")

    print(f"\n🏁 Completed processing {pdf_count} PDFs. Total appointments processed: {total_processed}")
    return total_processed

# ---------- MAIN ----------
if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y%m%d")
    initialize_db()  # ensure table exists + clean old records

    for folder_name in os.listdir(BASE_DIR):
        folder_path = os.path.join(BASE_DIR, folder_name)
        if os.path.isdir(folder_path) and folder_name.startswith(current_date + "-"):
            print(f"📂 Found today’s folder: {folder_path}")
            process_pdfs_in_directory(folder_path)
