-- Check which columns from the ORM models are missing from your database tables
-- Run these queries to see what columns need to be added

-- ============================================================================
-- FUNDING TABLE
-- ============================================================================
-- Check for missing columns
SHOW COLUMNS FROM funding LIKE 'project_status';

-- The ORM expects 'project_status' but if it's missing, you'll need to add it:
-- ALTER TABLE funding ADD COLUMN project_status VARCHAR(255) NULL;

-- ============================================================================
-- MEMBERSHIP TABLE
-- ============================================================================
-- Check for missing columns
SHOW COLUMNS FROM membership LIKE 'rlogx_id';

-- The ORM expects 'rlogx_id' but if it's missing, you'll need to add it:
-- ALTER TABLE membership ADD COLUMN rlogx_id INT NULL;

-- ============================================================================
-- PUBLICATIONS TABLE
-- ============================================================================
-- The 'research_program_abbrv' field is computed during transformation
-- but not stored in the database. This is correct - the code has been fixed
-- to not try to insert it.

-- ============================================================================
-- Check all tables for common missing columns
-- ============================================================================

-- Funding
SELECT 'funding' as table_name, 'project_status' as missing_column
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'funding' 
    AND COLUMN_NAME = 'project_status'
);

-- Membership
SELECT 'membership' as table_name, 'rlogx_id' as missing_column
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'membership' 
    AND COLUMN_NAME = 'rlogx_id'
);

