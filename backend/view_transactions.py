"""
view_transactions.py - View all transactions in a nice table format

HOW TO RUN:
  .\.venv\Scripts\python.exe backend/view_transactions.py
"""

import pymysql
from tabulate import tabulate

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
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Get all transactions
cursor.execute("""
    SELECT transaction_date, description, amount, transaction_type 
    FROM transactions 
    ORDER BY transaction_date DESC
""")

rows = cursor.fetchall()

# Display as table
headers = ["Date", "Description", "Amount", "Type"]
print("\n" + "=" * 100)
print(f"ALL TRANSACTIONS ({len(rows)} total)")
print("=" * 100 + "\n")
print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
print(f"\n✓ Total rows: {len(rows)}")

# Summary stats
cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount < 0")
total_spent = cursor.fetchone()[0] or 0

cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0")
total_deposits = cursor.fetchone()[0] or 0

print(f"\n{'─' * 50}")
print(f"Total Spent:    ${abs(total_spent):>12,.2f}")
print(f"Total Deposits: ${total_deposits:>12,.2f}")
print(f"Net:            ${(total_deposits + total_spent):>12,.2f}")
print(f"{'─' * 50}\n")

cursor.close()
conn.close()
