"""
run_03_transform.py - Transform staging data into final transactions table

WHAT THIS DOES:
  Takes data from transactions_staging and normalizes it:
  - Parses dates
  - Cleans up amounts
  - Inserts into final transactions table

HOW TO RUN:
  .\.venv\Scripts\python.exe backend/run_03_transform.py

EXPECTED OUTPUT:
  ✓ Successfully transformed and inserted 233 rows
"""

import pymysql
import os

print("=" * 70)
print("STEP 3: Transform and Load Final Data")
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
    print("  Make sure MySQL server is running")
    exit(1)

# Execute the transformation SQL
try:
    # Transform: Parse dates and amounts, then insert into final transactions table
    sql = """
    INSERT INTO transactions (transaction_date, post_date, description, amount, transaction_type, memo)
    SELECT 
        STR_TO_DATE(transaction_date, '%m/%d/%Y') as transaction_date,
        STR_TO_DATE(post_date, '%m/%d/%Y') as post_date,
        description,
        CAST(REPLACE(REPLACE(amount, '$', ''), ',', '') AS DECIMAL(12, 2)) as amount,
        type as transaction_type,
        memo
    FROM transactions_staging
    """
    
    cursor.execute(sql)
    conn.commit()
    rows_inserted = cursor.rowcount
    print(f"✓ Successfully transformed and inserted {rows_inserted} rows")
    
except Exception as e:
    print(f"✗ SQL execution failed: {e}")
    exit(1)

# Show results
print("\n" + "-" * 70)
print("RESULTS:")
print("-" * 70)

try:
    # Count final transactions
    cursor.execute("SELECT COUNT(*) as cnt FROM transactions")
    count = cursor.fetchone()[0]
    print(f"✓ Total transactions in final table: {count}")
    
    # Show sample
    cursor.execute("""
        SELECT transaction_date, description, amount 
        FROM transactions 
        LIMIT 5
    """)
    rows = cursor.fetchall()
    print(f"\n  Sample of first 5 transactions:")
    for row in rows:
        desc = row[1][:40] if row[1] else "N/A"
        print(f"    {row[0]} | {desc:<40} | {row[2]}")
    
    # Show any errors
    cursor.execute("SELECT COUNT(*) as cnt FROM staging_errors")
    error_count = cursor.fetchone()[0]
    if error_count > 0:
        print(f"\n  ⚠ {error_count} rows had errors (see staging_errors table)")
except Exception as e:
    print(f"✗ Query failed: {e}")

cursor.close()
conn.close()

print("\n" + "=" * 70)
print("✓ COMPLETE! Your data is ready in the 'fintrack' database")
print("=" * 70)
print("\nYou can now:")
print("  - Query transactions with SQL")
print("  - Build reports or dashboards")
print("  - Set up your API/web interface")
print("\nDatabase: fintrack")
print("Tables: transactions, categories, customers")
print("=" * 70)
