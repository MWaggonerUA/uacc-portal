-- Check which columns from the ORM model are missing from your budgets table
-- Run this to see what columns need to be added

-- First, let's see what columns you currently have
SHOW COLUMNS FROM budgets;

-- The ORM model expects these columns. Compare with your table above:
-- Required metadata columns (you already added these):
--   upload_timestamp
--   source_filename  
--   upload_batch_id
--   created_at

-- Data columns that might be missing:
--   research_programs (VARCHAR(255) NULL)  <-- This one is definitely missing based on your error

