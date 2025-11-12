"""
connector.py - Load CSV into MySQL fintrack database via SQLAlchemy + pandas

WHAT THIS DOES:
  1. Reads your Chase CSV file
  2. Loads it into transactions_staging table
  3. Prints confirmation and row count

WORKFLOW:
  Step 1: Run this file to load CSV into staging
  Step 2: Run 03_transform_to_transactions.sql to clean and normalize
  Step 3: Data appears in the final transactions table

REQUIREMENTS:
  - MySQL server running with fintrack database
  - Tables created by 01_create_schema.sql
  - pandas, sqlalchemy, pymysql installed (pip install pandas sqlalchemy pymysql)
"""

import pandas as pd
from sqlalchemy import create_engine
import os

print("=" * 70)
print("CSV LOADER: Chase → MySQL fintrack.transactions_staging")
print("=" * 70)

# ============================================================================
# STEP 1: Build database connection URL
# ============================================================================

# Your MySQL credentials (update if different)
MYSQL_USER = "root"
MYSQL_PASSWORD = "ABGdbgcoldstone67@"
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "fintrack"

# Build SQLAlchemy URL
# Format: mysql+pymysql://user:password@host/database
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"

try:
    engine = create_engine(DATABASE_URL, echo=False)
    print(f"✓ Connected to MySQL: {MYSQL_HOST}/{MYSQL_DATABASE}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("  Check:")
    print("  - MySQL server is running")
    print("  - Database 'fintrack' exists (run 01_create_schema.sql)")
    print("  - Username and password are correct")
    exit(1)

# ============================================================================
# STEP 2: Read CSV file
# ============================================================================

csv_path = r"C:\Users\dexte\Downloads\Chase7561_Activity20250101_20251031_20251031.CSV"

if not os.path.exists(csv_path):
    print(f"✗ CSV file not found: {csv_path}")
    exit(1)
#This is the last piece I have updated with this comment, I know what this means 11-12-2025-12:14AM
print(f"✓ Reading CSV: {csv_path}")
df = pd.read_csv(csv_path, dtype=str)  # Read as strings to preserve format
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

# ============================================================================
# STEP 3: Load into staging table
# ============================================================================

print(f"Loading into transactions_staging...")
try:
    df_renamed.to_sql(
        'transactions_staging',
        con=engine,
        if_exists='append',      # Append to existing table (don't drop)
        index=False,             # Don't add an extra index column
        method='multi',          # Use multi-row insert (faster)
        chunksize=500            # Insert in batches of 500 rows
    )
    print(f"✓ Successfully inserted {len(df_renamed)} rows into staging table")
except Exception as e:
    print(f"✗ Insert failed: {e}")
    exit(1)

# ============================================================================
# STEP 4: Verify
# ============================================================================

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT COUNT(*) as cnt FROM transactions_staging")
        count = result.fetchone()[0]
        print(f"✓ Verified: {count} total rows in staging table")
except Exception as e:
    print(f"✗ Verification failed: {e}")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("1. Inspect the data in MySQL:")
print("   mysql -u root -p")
print("   USE fintrack;")
print("   SELECT * FROM transactions_staging LIMIT 5;")
print("")
print("2. Transform staging → transactions table:")
print("   mysql -u root -p fintrack < DatabaseMySQL/03_transform_to_transactions.sql")
print("")
print("3. Query your transactions:")
print("   SELECT COUNT(*) FROM transactions;")
print("   SELECT SUM(amount) FROM transactions;")
print("=" * 70)


