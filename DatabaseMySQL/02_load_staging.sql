-- ============================================================================
-- FILE: 02_load_staging.sql
-- PURPOSE: Load your Chase CSV file into the transactions_staging table
--
-- WHAT THIS DOES:
--   Reads the CSV file from your Downloads folder and inserts each row into
--   transactions_staging. The data stays in raw text format (as-is from CSV).
--   This is a "safe" first step because we don't modify or normalize anything yet.
--
-- WHY USE STAGING?
--   - Keeps raw data intact for auditing
--   - Lets you validate before modifying
--   - Easy to retry if something goes wrong
--   - Can re-run transforms without re-uploading CSV
--
-- HOW TO USE (Three options):
--
-- OPTION A (RECOMMENDED FOR BEGINNERS): Use Python to load
--   - Skip this file entirely
--   - Use the Python script: backend/connector.py (it will call this file's logic)
--   - Run: python backend/connector.py
--   
-- OPTION B: Use LOAD DATA LOCAL INFILE (fast but requires MySQL config)
--   - First run: SET GLOBAL local_infile = 1;
--   - Then: mysql -u root -p --local-infile < 02_load_staging.sql
--   - CAVEAT: Some MySQL setups don't allow this (security restriction)
--
-- OPTION C: Use MySQL Workbench or CLI (manual)
--   - Copy the LOAD DATA section below and paste into MySQL Workbench
--   - Change the file path to match your CSV location
--
-- IMPORTANT NOTES:
--   - The file path MUST use forward slashes (/) even on Windows
--   - The file path must be absolute (full path), not relative
--   - If CSV has different column order, adjust the column list at the end
--   - Line endings: CRLF is for Windows; use LF if your file is on Mac/Linux
--
-- ============================================================================

USE fintrack;

-- Clear staging if you want to reload (optional - comment out if doing first load)
-- DELETE FROM transactions_staging;

-- LOAD DATA LOCAL INFILE - Load your CSV into staging
-- IMPORTANT: Update the file path if your CSV is in a different location!
LOAD DATA LOCAL INFILE 'C:/Users/dexte/Downloads/Chase7561_Activity20250101_20251031_20251031.CSV'
INTO TABLE transactions_staging
FIELDS TERMINATED BY ','               -- CSV uses commas to separate columns
OPTIONALLY ENCLOSED BY '"'             -- Fields may be wrapped in quotes
LINES TERMINATED BY '\r\n'             -- Windows line ending (CRLF)
IGNORE 1 LINES                         -- Skip the header row
(@transaction_date, @post_date, @description, @category, @type, @amount, @memo)  -- Read all 7 columns
SET
  transaction_date = @transaction_date,
  post_date = @post_date,
  description = @description,
  category = @category,
  type = @type,
  amount = @amount,
  memo = @memo;

-- ============================================================================
-- VERIFY THE LOAD
-- ============================================================================

-- Check how many rows were loaded
SELECT CONCAT('Loaded ', COUNT(*), ' rows into staging') AS result
FROM transactions_staging;

-- Show the first 5 rows (to inspect)
SELECT * FROM transactions_staging LIMIT 5;

-- ============================================================================
-- NEXT STEP:
-- Run file: 03_transform_to_transactions.sql
-- (This will clean the data and move it to the final transactions table)
-- ============================================================================
