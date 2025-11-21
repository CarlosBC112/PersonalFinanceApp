-- Add username, password, and email columns to customers table
ALTER TABLE customers
  ADD COLUMN username VARCHAR(100) UNIQUE,
  ADD COLUMN password VARCHAR(100),
  ADD COLUMN email VARCHAR(255);

-- Insert new customer
INSERT INTO customers (
  account_number, account_type, holder_name, username, password, email
) VALUES (
  'ACC123456789', 'Checking', 'Carlos Bernal', 'MyFinances12345', 'AmrutaKudale', 'dexterthefirst112@gmail.com'
);
