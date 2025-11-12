-- ============================================================
-- STEP 1: CREATE DATABASE SCHEMA
-- ============================================================
-- This script creates the fintrack database and all required tables
-- Run this FIRST before loading data
-- ============================================================

-- Drop existing database if it exists (optional)
-- DROP DATABASE IF EXISTS fintrack;

-- Create the database
CREATE DATABASE IF NOT EXISTS fintrack;
USE fintrack;

-- ============================================================
-- TABLE 1: Categories
-- ============================================================
-- Stores expense categories (Shopping, Utilities, Gas, etc.)
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: Customers
-- ============================================================
-- Stores customer/account information
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(50) UNIQUE,
    account_type VARCHAR(50),
    holder_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 3: Transactions Staging
-- ============================================================
-- Raw data from CSV before transformation
-- This table holds untransformed data for audit/review
CREATE TABLE IF NOT EXISTS transactions_staging (
    staging_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_date VARCHAR(50),
    post_date VARCHAR(50),
    description VARCHAR(500),
    category VARCHAR(100),
    type VARCHAR(50),
    amount VARCHAR(50),
    memo VARCHAR(255),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 4: Transactions (Final)
-- ============================================================
-- Cleaned and normalized transaction data
-- This is the main table for reporting/analysis
CREATE TABLE IF NOT EXISTS transactions (
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
    
    -- Foreign keys for referential integrity
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    
    -- Indexes for performance
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_category_id (category_id),
    INDEX idx_customer_id (customer_id)
);

-- ============================================================
-- TABLE 5: Staging Errors
-- ============================================================
-- Records rows that couldn't be transformed
-- Useful for debugging data issues
CREATE TABLE IF NOT EXISTS staging_errors (
    error_id INT AUTO_INCREMENT PRIMARY KEY,
    staging_id INT,
    error_message VARCHAR(500),
    error_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (staging_id) REFERENCES transactions_staging(staging_id)
);

-- ============================================================
-- Sample category data (optional)
-- ============================================================
-- Uncomment the lines below to insert sample categories
-- INSERT INTO categories (category_name, description) VALUES
-- ('Shopping', 'Retail and shopping expenses'),
-- ('Utilities', 'Electric, water, gas bills'),
-- ('Groceries', 'Food and grocery shopping'),
-- ('Transportation', 'Gas and vehicle expenses'),
-- ('Entertainment', 'Movies, dining, entertainment'),
-- ('Other', 'Miscellaneous expenses');

-- ============================================================
-- Verify tables were created
-- ============================================================
-- Run these queries to verify:
-- SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'fintrack';
-- SHOW TABLES;

COMMIT;
