# MySQL + CSV Import Setup Guide

**For Beginners: A Complete Step-by-Step Workflow**

---

## Overview

You have **3 SQL files** and **1 Python script**. They work together to:
1. Create database structure
2. Load your CSV file
3. Clean and normalize the data
4. Store it in your final transactions table

---

## Files Explained

### 📁 `DatabaseMySQL/01_create_schema.sql`
**What it does:** Creates the database structure (tables)

**Think of it like:** Building a filing cabinet with labeled drawers

**What's inside:**
- `fintrack` database - your main database
- `customers` table - stores user accounts
- `categories` table - stores transaction categories (Groceries, Gas, etc)
- `transactions` table - **this is where your final data goes**
- `transactions_staging` table - temporary holding area for CSV data
- `staging_errors` table - logs rows that had problems

**When to run:** First time only (before loading any data)

**How to run:**
```powershell
mysql -u root -p < DatabaseMySQL/01_create_schema.sql
# When prompted, enter your MySQL root password
```

---

### 📁 `DatabaseMySQL/02_load_staging.sql`
**What it does:** Loads your CSV file into the staging table

**Think of it like:** Photocopying a document before you file it

**Why staging?**
- Keeps original CSV data intact
- Lets you validate before moving to final table
- Easy to re-try if something goes wrong

**When to run:** After running 01_create_schema.sql, but **DON'T use this file directly**

**Why not?** Because the Python script (connector.py) does this job better and easier

---

### 📁 `DatabaseMySQL/03_transform_to_transactions.sql`
**What it does:** Cleans the data and moves it to the final transactions table

**Think of it like:** Taking messy notes and filing them properly in a folder

**What it cleans:**
- Dates: `"10/27/2025"` → `2025-10-27` (database format)
- Amounts: `"$1,234.56"` → `1234.56` (number format)
- Negatives: `"(100)"` → `-100` (parentheses → minus sign)

**When to run:** After running connector.py

**How to run:**
```powershell
mysql -u root -p fintrack < DatabaseMySQL/03_transform_to_transactions.sql
```

---

### 🐍 `backend/connector.py`
**What it does:** Reads your CSV and loads it into the staging table (replaces manual 02_load_staging.sql)

**Think of it like:** An automated assistant that feeds data into the filing cabinet

**What it does step-by-step:**
1. Connects to MySQL
2. Reads your Chase CSV file
3. Renames CSV columns to match database schema
4. Inserts rows into `transactions_staging`
5. Shows you results

**When to run:** After running 01_create_schema.sql

**How to run:**
```powershell
cd "C:\Users\dexte\Finance Project CS"
.\.venv\Scripts\python.exe backend/connector.py
```

**What you'll see:**
```
======================================================================
CSV LOADER: Chase → MySQL fintrack.transactions_staging
======================================================================
✓ Connected to MySQL: localhost/fintrack
✓ Reading CSV: C:\Users\dexte\Downloads\Chase7561_Activity20250101_20251031_20251031.CSV
✓ Loaded 233 rows from CSV
Loading into transactions_staging...
✓ Successfully inserted 233 rows into staging table
✓ Verified: 233 total rows in staging table

======================================================================
NEXT STEPS:
======================================================================
```

---

## 🚀 Complete Step-by-Step Workflow

### **Step 1: Create the database and tables**
```powershell
mysql -u root -p < DatabaseMySQL/01_create_schema.sql
```
**What this does:** Sets up the filing cabinet and creates all drawers

**When prompted:** Enter your MySQL root password (`ABGdbgcoldstone67@`)

**Check if it worked:** 
```powershell
mysql -u root -p
mysql> USE fintrack;
mysql> SHOW TABLES;
```
You should see 5 tables listed.

---

### **Step 2: Load CSV into staging**
```powershell
cd "C:\Users\dexte\Finance Project CS"
.\.venv\Scripts\python.exe backend/connector.py
```
**What this does:** Reads your CSV and puts it in the staging table

**Expected output:** Something like `✓ Successfully inserted 233 rows into staging table`

**Check if it worked:**
```powershell
mysql -u root -p
mysql> USE fintrack;
mysql> SELECT COUNT(*) FROM transactions_staging;
```
Should show your row count (233 or however many rows).

---

### **Step 3: Transform and move to final table**
```powershell
mysql -u root -p fintrack < DatabaseMySQL/03_transform_to_transactions.sql
```
**What this does:** Cleans the data and moves it to the final `transactions` table

**Expected output:** Shows summary and sample rows

**Check if it worked:**
```powershell
mysql -u root -p
mysql> USE fintrack;
mysql> SELECT COUNT(*) FROM transactions;
mysql> SELECT * FROM transactions LIMIT 5;
```

---

## 📊 Query Examples (After data is loaded)

**Count total transactions:**
```sql
SELECT COUNT(*) FROM transactions;
```

**Total amount spent:**
```sql
SELECT SUM(amount) FROM transactions;
```

**Transactions in October 2025:**
```sql
SELECT * FROM transactions 
WHERE date_of_purchase >= '2025-10-01' 
  AND date_of_purchase < '2025-11-01';
```

**Spending by category:**
```sql
SELECT category, SUM(amount) as total
FROM transactions
GROUP BY category
ORDER BY total DESC;
```

---

## ⚠️ Common Issues & Fixes

### Issue: "Access Denied for user 'root'"
**Fix:** Make sure you're using the correct password. Change `ABGdbgcoldstone67@` if your password is different.

### Issue: "Database 'fintrack' doesn't exist"
**Fix:** Run Step 1 first (`01_create_schema.sql`)

### Issue: "File not found: Chase7561_..."
**Fix:** Make sure your CSV is in `C:\Users\dexte\Downloads\` or update the path in `connector.py`

### Issue: "Local infile is disabled"
**Fix:** Don't worry - connector.py doesn't use LOAD DATA INFILE. It uses pandas instead.

### Issue: Column name mismatches
**Fix:** If your CSV has different column names, edit the `rename()` section in connector.py

---

## 🔄 After First Load (Running Again)

If you have a new CSV or want to reload:

**Option A: Clear and reload**
```sql
TRUNCATE TABLE transactions_staging;
TRUNCATE TABLE transactions;
```
Then run connector.py and step 3 again.

**Option B: Append (add to existing data)**
Just run connector.py and step 3 again - it will append new rows.

---

## 📋 Data Dictionary

### transactions table columns:
| Column | Meaning | Example |
|--------|---------|---------|
| `id` | Unique transaction ID | 1, 2, 3... |
| `customer_id` | Which customer | "unknown" (for now) |
| `date_of_purchase` | When transaction happened | 2025-10-27 |
| `item_description` | What was purchased | "STARBUCKS COFFEE" |
| `category` | Type of spending | "Food and Drink" |
| `amount` | How much | -5.50 (negative = spending) |
| `created_at` | When data was entered | 2025-11-11 10:00:00 |

---

## 🎯 Next Steps

1. ✅ Run all 3 steps above
2. ✅ Query and explore your data
3. ✅ Build reports or dashboards
4. ✅ Integrate with your API

---

## 💡 Tips

- **Backup your data:** Always backup before running transformations
- **Test first:** Run with a small CSV first to learn the process
- **Read error messages:** They tell you what went wrong
- **Use comments:** I've added comments to all SQL files to help you learn

---

## ❓ Still Confused?

Remember:
- **01_create_schema.sql** = Create the structure
- **connector.py** = Load the data
- **03_transform_to_transactions.sql** = Clean the data

Run them in order, and everything works!
