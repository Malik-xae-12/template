
import re
import sys
from datetime import datetime
import os
import pdfplumber
import pyodbc
from typing import List, Tuple
import re
import sys
from datetime import datetime
import os
import pdfplumber
import pyodbc
from typing import List, Tuple

# ---------- CONFIG ----------
SQL_SERVER = 
SQL_DATABASE = 
SQL_USERNAME = 
SQL_PASSWORD = 
SQL_DRIVER = '{ODBC Driver 17 for SQL Server}'
BATCH_SIZE = 1000
BASE_DIR = r"E:\TC_BC\Appointments"   # <---- base directory
# ----------------------------

INSERT_SQL = """
INSERT INTO dbo.appointments
    (urn, care_provider, location, gender, patient_name, start_date, end_date, timestamp, pdf_path)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

CREATE_TABLE_SQL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'appointments' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.appointments (
        id INT IDENTITY(1,1) PRIMARY KEY,
        urn NVARCHAR(50) NULL,
        care_provider NVARCHAR(255) NULL,
        location NVARCHAR(255) NULL,
        gender CHAR(1) NULL,
        patient_name NVARCHAR(255) NULL,
        start_date DATE NULL,
        end_date DATE NULL,
        timestamp DATETIME2(0) NULL,
        pdf_path NVARCHAR(255) NULL,
        created_at DATETIME2(0) DEFAULT SYSUTCDATETIME()
    );
END
"""

# ✅ Index creation (runs after table is ensured)
CREATE_INDEXES_SQL = [
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_start_date') CREATE INDEX idx_appt_start_date ON dbo.appointments (start_date);",
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_timestamp') CREATE INDEX idx_appt_timestamp ON dbo.appointments (timestamp);",
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_urn') CREATE INDEX idx_appt_urn ON dbo.appointments (urn);",
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_care_provider') CREATE INDEX idx_appt_care_provider ON dbo.appointments (care_provider);",
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_patient_name') CREATE INDEX idx_appt_patient_name ON dbo.appointments (patient_name);",
    "IF NOT EXISTS (SELECT name FROM sys.indexes WHERE name='idx_appt_location') CREATE INDEX idx_appt_location ON dbo.appointments (location);",
]

def get_connection():
    conn_str = f"DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}"
    return pyodbc.connect(conn_str, autocommit=False)

def extract_text_with_pdfplumber(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return None
    all_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    all_text += f"\n--- Page {page_num} ---\n{text}"
                    print(f"✅ Extracted page {page_num} from {pdf_path}")
        return all_text
    except Exception as e:
        print(f"❌ Error extracting PDF {pdf_path}: {e}")
        return None

def ensure_table_and_indexes(cursor):
    """Ensure table and indexes exist."""
    cursor.execute(CREATE_TABLE_SQL)
    for sql in CREATE_INDEXES_SQL:
        cursor.execute(sql)

def save_appointments_from_text(extracted_text: str, pdf_path: str) -> int:
    if not extracted_text:
        print(f"❌ No text to process for {pdf_path}")
        return 0

    try:
        conn = get_connection()
        cursor = conn.cursor()
        ensure_table_and_indexes(cursor)
        conn.commit()
        cursor.fast_executemany = True
    except pyodbc.Error as e:
        print(f"❌ Failed to connect to SQL Server: {e}")
        return 0

    period_start, period_end = None, None
    current_care_provider, current_location = None, None
    appointments_processed = 0
    batch_rows: List[Tuple] = []

    lines = extracted_text.splitlines()
    print(f"📝 Processing {len(lines)} lines of text from {pdf_path}...")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Period
        if line.startswith("Period:") and period_start is None:
            match = re.search(r"Period:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", line)
            if match:
                try:
                    period_start = datetime.strptime(match.group(1), '%d/%m/%Y').date()
                    period_end = datetime.strptime(match.group(2), '%d/%m/%Y').date()
                    print(f"✅ Period set: {period_start} to {period_end}")
                except Exception as e:
                    print(f"⚠️ Error parsing period: {e}")
                    period_start = period_end = datetime.now().date()
            else:
                period_start = period_end = datetime.now().date()
            continue

        # Care Provider
        if line.startswith("Care Provider:") or line.startswith("Care Provider/Resource:"):
            current_care_provider = line.split(":", 1)[-1].strip()
            continue

        # Location
        if line.startswith("Location:"):
            current_location = line.split(":", 1)[-1].strip()
            continue

        # Appointment rows
        if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", line):
            period_start = period_start or datetime.now().date()
            period_end = period_end or period_start
            current_care_provider = current_care_provider or "Unknown Provider"
            current_location = current_location or "Unknown Location"

            try:
                parts = line.split()
                date_part, time_part, urn = parts[0], parts[1], parts[2][:-1] if parts[2] else None

                # Patient + gender
                patient_name_parts, gender = [], None
                for token in parts[3:]:
                    if re.match(r"\d{10,}", token):
                        break
                    if token.lower() in ['transferred','booked','new','patient','visit','follow','up','established']:
                        break
                    if token in ['M', 'F'] and gender is None:
                        gender = token
                    else:
                        patient_name_parts.append(token)

                patient_name = " ".join(patient_name_parts).strip()
                gender = gender or "U"
                timestamp = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")

                batch_rows.append((
                    urn, current_care_provider, current_location,
                    gender, patient_name, period_start, period_end, timestamp, pdf_path
                ))

                if len(batch_rows) >= BATCH_SIZE:
                    cursor.executemany(INSERT_SQL, batch_rows)
                    conn.commit()
                    appointments_processed += len(batch_rows)
                    print(f"🔁 Committed batch of {len(batch_rows)} rows.")
                    batch_rows = []

            except Exception as e:
                print(f"⚠️ Error processing line: {line}\n{e}")
                continue

    # final flush
    if batch_rows:
        try:
            cursor.executemany(INSERT_SQL, batch_rows)
            conn.commit()
            appointments_processed += len(batch_rows)
            print(f"🔁 Committed final batch of {len(batch_rows)} rows.")
        except Exception as e:
            print(f"❌ Error committing final batch: {e}")
            conn.rollback()

    conn.close()
    return appointments_processed

def process_pdfs_in_directory(base_dir: str):
    total_pdfs, total_rows = 0, 0
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                print(f"\n📄 Processing {pdf_path}")
                extracted_text = extract_text_with_pdfplumber(pdf_path)
                if extracted_text:
                    inserted = save_appointments_from_text(extracted_text, pdf_path)
                    total_rows += inserted
                total_pdfs += 1
    print(f"\n🏁 Done. Processed {total_pdfs} PDFs. Inserted {total_rows} rows.")
    return total_rows

# ---------- MAIN ----------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            process_pdfs_in_directory(path)
        else:
            extracted_text = extract_text_with_pdfplumber(path)
            if extracted_text:
                save_appointments_from_text(extracted_text, path)
    else:
        process_pdfs_in_directory(BASE_DIR)
