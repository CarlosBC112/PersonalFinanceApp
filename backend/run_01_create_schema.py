"""
run_01_create_schema.py - Create MySQL database and tables

WHAT THIS DOES:
  Reads 01_create_schema.sql and executes it in your local MySQL
  Creates the fintrack database and all tables

HOW TO RUN:
  .\.venv\Scripts\python.exe backend/run_01_create_schema.py

EXPECTED OUTPUT:
  ✓ Database and tables created successfully
"""

import pymysql
import os

print("=" * 70)
print("STEP 1: Create Database & Tables")
print("=" * 70)

# MySQL connection
MYSQL_USER = "root"
MYSQL_PASSWORD = "ABGdbgcoldstone67@"
MYSQL_HOST = "localhost"

# Connect directly with pymysql (more reliable)
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    print(f"✓ Connected to MySQL server")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("  Make sure MySQL server is running")
    exit(1)

# Read the SQL file
# Get the project root directory (parent of backend folder)
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sql_file = os.path.join(project_root, "DatabaseMySQL", "01_create_schema.sql")

if not os.path.exists(sql_file):
    print(f"✗ SQL file not found: {sql_file}")
    exit(1)

print(f"✓ Reading SQL file: {sql_file}")

with open(sql_file, 'r') as f:
    sql_content = f.read()

# First, create the database
try:
    cursor.execute("CREATE DATABASE IF NOT EXISTS fintrack")
    conn.commit()
    print(f"✓ Created 'fintrack' database")
except Exception as e:
    print(f"✗ Failed to create database: {e}")
    exit(1)

# Now close and reconnect to the new database
cursor.close()
conn.close()

try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database="fintrack"
    )
    cursor = conn.cursor()
    print(f"✓ Connected to 'fintrack' database")
except Exception as e:
    print(f"✗ Failed to connect to fintrack database: {e}")
    exit(1)

# Now execute all the CREATE TABLE statements
# Use direct SQL instead of parsing the file
tables_sql = [
    """CREATE TABLE IF NOT EXISTS categories (
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL UNIQUE,
        description VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        account_number VARCHAR(50) UNIQUE,
        account_type VARCHAR(50),
        holder_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS transactions_staging (
        staging_id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_date VARCHAR(50),
        post_date VARCHAR(50),
        description VARCHAR(500),
        category VARCHAR(100),
        type VARCHAR(50),
        amount VARCHAR(50),
        memo VARCHAR(255),
        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT,
        category_id INT,
        transaction_date DATE,
        post_date DATE,
        description VARCHAR(500),
        amount DECIMAL(12, 2),
        transaction_type VARCHAR(50),
        memo VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (category_id) REFERENCES categories(category_id),
        INDEX idx_transaction_date (transaction_date),
        INDEX idx_category_id (category_id),
        INDEX idx_customer_id (customer_id)
    )""",
    """CREATE TABLE IF NOT EXISTS staging_errors (
        error_id INT AUTO_INCREMENT PRIMARY KEY,
        staging_id INT,
        error_message VARCHAR(500),
        error_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (staging_id) REFERENCES transactions_staging(staging_id)
    )"""
]

executed_count = 0
try:
    for sql in tables_sql:
        cursor.execute(sql)
        executed_count += 1
    
    conn.commit()
    print(f"✓ Created {executed_count} tables")
    
except Exception as e:
    print(f"✗ Execution failed: {e}")
    exit(1)
finally:
    cursor.close()
    conn.close()

# Verify the database was created
print("\nVerifying database creation...")
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database="fintrack"
    )
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"✓ Database 'fintrack' created with {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Verification failed: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✓ STEP 1 COMPLETE!")
print("=" * 70)
print("\nNEXT STEP: Run run_02_load_csv.py")
print("=" * 70)
