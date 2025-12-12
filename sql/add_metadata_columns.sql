-- Add upload metadata columns to budgets table
-- Run this SQL on your database to add the missing columns
-- 
-- This will add the columns and set default values for existing rows

-- Add columns (nullable first, then we'll set defaults)
ALTER TABLE budgets
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

-- Set default values for existing rows
UPDATE budgets 
SET 
    upload_timestamp = CURRENT_TIMESTAMP,
    source_filename = 'legacy_import',
    created_at = CURRENT_TIMESTAMP
WHERE upload_timestamp IS NULL;

-- Now make them NOT NULL (if your MySQL version supports it)
-- For older MySQL versions, you may need to manually make them NOT NULL via ALTER
ALTER TABLE budgets
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Add indexes for better query performance
-- Note: If the index already exists, you'll get an error - that's okay, just skip it
CREATE INDEX idx_budgets_upload_timestamp ON budgets(upload_timestamp);

-- Verify the columns were added
DESCRIBE budgets;

