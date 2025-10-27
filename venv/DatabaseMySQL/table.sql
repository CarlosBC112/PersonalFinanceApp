-- 1) Customers table (secure + normalized)
CREATE TABLE customers (
  id CHAR(36) NOT NULL PRIMARY KEY,            -- store UUID strings
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone_number VARCHAR(30),
  username VARCHAR(100) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,        -- store hash (bcrypt/argon2)
  customer_identification VARCHAR(100),       -- e.g. last 4 or masked id; DO NOT store full account numbers
  total_spending DECIMAL(13,2) DEFAULT 0.00,  -- computed/summary field (optional)
  rough_monthly_income DECIMAL(13,2),         -- numeric, nullable if unknown
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) Categories table (master list)
CREATE TABLE categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Transactions / Customer Finance (expenditure lines)
CREATE TABLE transactions (
  id BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  customer_id CHAR(36) NOT NULL,
  date_of_purchase DATE NOT NULL,
  item_description VARCHAR(500),
  category_id INT,                             -- nullable until classified
  amount DECIMAL(13,2) NOT NULL,               -- positive for expense amount; use sign convention in app
  currency CHAR(3) DEFAULT 'USD',
  source VARCHAR(100),                          -- e.g. "Chase PDF", "Manual upload"
  parsed_raw TEXT,                              -- original parsed text for debugging
  category_source ENUM('rule','ai','manual') DEFAULT 'rule',
  ai_confidence FLOAT,                          -- nullable: store AI confidence if used
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Indexes for reporting
CREATE INDEX idx_transactions_customer_date ON transactions(customer_id, date_of_purchase);
CREATE INDEX idx_transactions_category ON transactions(category_id);
