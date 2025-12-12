-- Check funding table data without assuming 'id' column exists
-- This will show what columns actually exist and what data is there

-- First, show what columns exist in the funding table
SHOW COLUMNS FROM funding;

-- Then check the actual data
SELECT 
    upload_timestamp, 
    source_filename,
    project_id,
    project_uid, 
    project_title, 
    grant_number,
    project_begin,
    project_end,
    fiscal_year,
    master_fund,
    training_project
FROM funding 
WHERE project_uid LIKE 'SMOKE%' 
   OR source_filename LIKE '%test%'
   OR upload_timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY upload_timestamp DESC 
LIMIT 5;

