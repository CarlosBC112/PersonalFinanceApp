-- ============================================================================
-- FILE: 03_transform_to_transactions.sql
-- PURPOSE: Clean and normalize data from staging, then insert into transactions
--
-- WHAT THIS DOES:
--   1. Reads raw data from transactions_staging
--   2. Cleans/normalizes:
--      - Date strings (e.g., "10/27/2025") → DATE format (2025-10-27)
--      - Amount strings (e.g., "$1,234.56" or "(100)") → DECIMAL with correct sign
--   3. Inserts cleaned rows into the final transactions table
--   4. Logs any bad rows to staging_errors table
--
-- WHY NORMALIZE?
--   - Database stores dates/numbers in specific formats for queries
--   - Makes calculations and filtering easier later
--   - Removes currency symbols and fixes negative amounts
--
-- HOW TO USE:
--   Copy and paste into MySQL Workbench or CLI:
--   mysql -u root -p fintrack < 03_transform_to_transactions.sql
--
-- ============================================================================

USE fintrack;

-- ============================================================================
-- STEP 1: Move valid rows from staging → transactions (with normalization)
-- ============================================================================

INSERT INTO transactions (
  customer_id,
  date_of_purchase,
  item_description,
  category,
  type,
  amount,
  currency,
  source,
  parsed_raw
)
SELECT
  'unknown' AS customer_id,                    -- Default customer (no login yet)
  STR_TO_DATE(s.transaction_date, '%m/%d/%Y') AS date_of_purchase,  -- Convert "10/27/2025" → 2025-10-27
  s.description AS item_description,          -- Keep merchant name as-is
  s.category,                                 -- Category from CSV
  s.type,                                     -- Type from CSV (Sale, Payment)
  -- Normalize amount: remove $, convert parentheses to negative, parse to decimal
  CAST(
    REPLACE(
      REPLACE(
        CASE
          WHEN TRIM(s.amount) LIKE '(%' THEN 
            CONCAT('-', TRIM(BOTH '()' FROM TRIM(s.amount)))
          ELSE 
            TRIM(s.amount)
        END
      , '$', '')
    , ',', '')
  AS DECIMAL(13,2)) AS amount,
  'USD' AS currency,                          -- Default currency
  'csv' AS source,                            -- Mark source as CSV
  CONCAT(
    'original_raw={date:', s.transaction_date,
    ', post_date:', s.post_date,
    ', amount:', s.amount,
    ', memo:', COALESCE(s.memo,'')
    ,'}'
  ) AS parsed_raw                             -- Keep original values for audit
FROM transactions_staging s
WHERE
  -- Only insert valid rows (has date and amount)
  COALESCE(TRIM(s.transaction_date), '') <> ''
  AND COALESCE(TRIM(s.amount), '') <> ''
  -- Date must be parseable (avoid bad dates)
  AND STR_TO_DATE(s.transaction_date, '%m/%d/%Y') IS NOT NULL
ORDER BY s.id;

-- ============================================================================
-- STEP 2: Log rows that failed (for debugging)
-- ============================================================================

INSERT INTO staging_errors (staging_id, error_text)
SELECT 
  id,
  CONCAT(
    'Failed validation: ',
    CASE
      WHEN COALESCE(TRIM(transaction_date), '') = '' THEN 'missing date'
      WHEN COALESCE(TRIM(amount), '') = '' THEN 'missing amount'
      WHEN STR_TO_DATE(transaction_date, '%m/%d/%Y') IS NULL THEN CONCAT('bad date format: ', transaction_date)
      ELSE 'unknown error'
    END
  ) AS error_text
FROM transactions_staging s
WHERE
  -- Match rows that were NOT inserted above
  (COALESCE(TRIM(s.transaction_date), '') = ''
   OR COALESCE(TRIM(s.amount), '') = ''
   OR STR_TO_DATE(s.transaction_date, '%m/%d/%Y') IS NULL);

-- ============================================================================
-- STEP 3: Show results
-- ============================================================================

SELECT CONCAT(
  'Summary: ',
  (SELECT COUNT(*) FROM transactions) , ' transactions inserted, ',
  (SELECT COUNT(*) FROM staging_errors), ' errors logged'
) AS result;

-- Show sample of inserted transactions
SELECT 'Sample of inserted transactions:' AS info;
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;

-- Show any errors
SELECT 'Errors (if any):' AS info;
SELECT * FROM staging_errors LIMIT 10;

-- ============================================================================
-- DONE! Your data is now in the transactions table.
-- 
-- NEXT STEPS:
--   1. Verify the data looks correct (check the sample output above)
--   2. Query your data:
--      SELECT COUNT(*) FROM transactions;
--      SELECT SUM(amount) FROM transactions;
--      SELECT * FROM transactions WHERE date_of_purchase >= '2025-10-01';
--   3. Update connector.py or csv_ingest.py to automate this in the future
--   4. (Optional) Delete staging table when you're confident: DROP TABLE transactions_staging;
-- ============================================================================
