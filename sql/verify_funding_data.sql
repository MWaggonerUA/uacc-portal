-- Verify which columns actually have data in the funding table
-- This will show only non-NULL values for the test records

SELECT 
    -- Metadata columns (should always have values)
    upload_timestamp,
    source_filename,
    
    -- Test data columns (check which ones have values)
    project_id,
    project_uid,
    project_title,
    grant_number,
    core_project_num,
    project_begin,
    project_end,
    fiscal_year,
    master_fund,
    training_project,
    peer_review_type,
    peer_review_type_id,
    project_status_id,
    import_source,
    multi_pi
    
FROM funding 
WHERE project_uid LIKE 'SMOKE%' 
   OR source_filename = 'test_db_funding.csv'
ORDER BY upload_timestamp DESC 
LIMIT 5;

-- Also check how many rows were inserted
SELECT COUNT(*) as total_test_rows 
FROM funding 
WHERE project_uid LIKE 'SMOKE%' 
   OR source_filename = 'test_db_funding.csv';

