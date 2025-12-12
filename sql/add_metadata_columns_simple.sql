-- Add upload metadata columns to budgets table
-- Run this SQL on your database to add the missing columns
-- 
-- For MySQL 5.7+ or MariaDB 10.2+

-- Step 1: Add columns (allow NULL initially for existing rows)
ALTER TABLE budgets
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

-- Step 2: Set default values for existing rows
UPDATE budgets 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

-- Step 3: Make columns NOT NULL (MySQL 5.7+ syntax)
ALTER TABLE budgets
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Step 4: Add index (drop first if it exists, then create)
DROP INDEX IF EXISTS idx_budgets_upload_timestamp ON budgets;
CREATE INDEX idx_budgets_upload_timestamp ON budgets(upload_timestamp);

-- Step 5: Verify
DESCRIBE budgets;

