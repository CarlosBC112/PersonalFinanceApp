"""
run_02_load_csv.py - Load CSV into staging table

WHAT THIS DOES:
  Reads your Chase CSV and loads it into transactions_staging

HOW TO RUN:
  .\.venv\Scripts\python.exe backend/run_02_load_csv.py

EXPECTED OUTPUT:
  ✓ Successfully inserted 233 rows into staging table
"""

import pandas as pd
import pymysql
import os

print("=" * 70)
print("STEP 2: Load CSV into Staging Table")
print("=" * 70)

# MySQL connection
MYSQL_USER = "root"
MYSQL_PASSWORD = "ABGdbgcoldstone67@"
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "fintrack"

try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()
    print(f"✓ Connected to MySQL: {MYSQL_HOST}/{MYSQL_DATABASE}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("  Make sure:")
    print("  - MySQL server is running")
    print("  - Database 'fintrack' exists (run run_01_create_schema.py first)")
    exit(1)

# Read CSV
csv_path = r"C:\Users\dexte\Downloads\Chase7561_Activity20250101_20251031_20251031.CSV"

if not os.path.exists(csv_path):
    print(f"✗ CSV file not found: {csv_path}")
    exit(1)

print(f"✓ Reading CSV: {csv_path}")
df = pd.read_csv(csv_path, dtype=str)
print(f"✓ Loaded {len(df)} rows from CSV")

# Rename columns to match database schema
df_renamed = df.rename(columns={
    "Transaction Date": "transaction_date",
    "Post Date": "post_date",
    "Description": "description",
    "Category": "category",
    "Type": "type",
    "Amount": "amount",
    "Memo": "memo"
})

# Load into staging
print(f"Loading into transactions_staging...")
try:
    # Insert rows one by one, handling NaN values
    for idx, row in df_renamed.iterrows():
        # Convert NaN to None (NULL in MySQL)
        row_values = [None if pd.isna(val) else val for val in row]
        
        sql = """
            INSERT INTO transactions_staging 
            (transaction_date, post_date, description, category, type, amount, memo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, tuple(row_values))
    
    conn.commit()
    print(f"✓ Successfully inserted {len(df_renamed)} rows into staging table")
except Exception as e:
    print(f"✗ Insert failed: {e}")
    exit(1)

# Verify
try:
    cursor.execute("SELECT COUNT(*) as cnt FROM transactions_staging")
    count = cursor.fetchone()[0]
    print(f"✓ Verified: {count} total rows in staging table")
except Exception as e:
    print(f"✗ Verification failed: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("NEXT STEP: Run run_03_transform.py")
print("=" * 70)
