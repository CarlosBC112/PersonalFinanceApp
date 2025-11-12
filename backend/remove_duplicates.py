"""
remove_duplicates.py - Remove duplicate rows from transactions table

What it does:
 - Connects to fintrack.transactions
 - Counts rows before
 - Runs a DELETE that removes rows where all key columns match and transaction_id is greater (keeps the lowest id)
 - Commits and reports how many rows were removed and final count

How to run:
 .\.venv\Scripts\python.exe backend/remove_duplicates.py

NOTE: This is destructive. If you want a backup first, export the table or create a copy.
"""

import pymysql

MYSQL_USER = "root"
MYSQL_PASSWORD = "ABGdbgcoldstone67@"
MYSQL_HOST = "localhost"
MYSQL_DATABASE = "fintrack"

delete_sql = """
DELETE t1 FROM transactions t1
INNER JOIN transactions t2
  ON t1.transaction_date <=> t2.transaction_date
  AND t1.post_date <=> t2.post_date
  AND t1.description <=> t2.description
  AND t1.amount <=> t2.amount
  AND t1.transaction_type <=> t2.transaction_type
  AND t1.memo <=> t2.memo
  AND t1.customer_id <=> t2.customer_id
  AND t1.category_id <=> t2.category_id
WHERE t1.transaction_id > t2.transaction_id
"""

print("Connecting to database...")
try:
    conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE)
    cursor = conn.cursor()
except Exception as e:
    print(f"Connection failed: {e}")
    raise SystemExit(1)

cursor.execute("SELECT COUNT(*) FROM transactions")
before = cursor.fetchone()[0]
print(f"Rows before: {before}")

print("Running duplicate removal SQL...")
try:
    deleted = cursor.execute(delete_sql)
    conn.commit()
    # cursor.rowcount may be -1 in some drivers, so try to get affected_rows from connection if available
    try:
        affected = cursor.rowcount
    except Exception:
        affected = deleted
    print(f"Rows deleted (cursor.rowcount): {affected}")
except Exception as e:
    print(f"Delete failed: {e}")
    conn.rollback()
    cursor.close()
    conn.close()
    raise SystemExit(1)

cursor.execute("SELECT COUNT(*) FROM transactions")
after = cursor.fetchone()[0]
print(f"Rows after: {after}")

cursor.close()
conn.close()
print("Done.")
