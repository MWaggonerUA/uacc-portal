-- Add missing columns to database tables
-- Run this SQL to add columns that the ORM models expect but are missing
-- Note: These ALTER TABLE statements will fail if columns already exist,
-- which is fine - just means they're already there.

-- ============================================================================
-- FUNDING TABLE
-- ============================================================================
-- Add project_status column if it doesn't exist
ALTER TABLE funding ADD COLUMN project_status VARCHAR(255) NULL;

-- Add project_id column if it doesn't exist (nullable data column, not primary key)
ALTER TABLE funding ADD COLUMN project_id INT NULL;

-- Add project_uid column if it doesn't exist
ALTER TABLE funding ADD COLUMN project_uid VARCHAR(255) NULL;

-- ============================================================================
-- MEMBERSHIP TABLE
-- ============================================================================
-- Add rlogx_id column if it doesn't exist
ALTER TABLE membership ADD COLUMN rlogx_id INT NULL;

-- Add member_id column if it doesn't exist (nullable data column, not primary key)
ALTER TABLE membership ADD COLUMN member_id INT NULL;

-- Add ccm_type_code column if it doesn't exist
ALTER TABLE membership ADD COLUMN ccm_type_code TEXT NULL;

-- ============================================================================
-- PUBLICATIONS TABLE
-- ============================================================================
-- Add publication_id column if it doesn't exist (nullable data column, not primary key)
ALTER TABLE publications ADD COLUMN publication_id INT NULL;

-- Add publication_uid column if it doesn't exist
ALTER TABLE publications ADD COLUMN publication_uid VARCHAR(255) NULL;

-- Add pub_type column if it doesn't exist
ALTER TABLE publications ADD COLUMN pub_type VARCHAR(255) NULL;

-- ============================================================================
-- VERIFY
-- ============================================================================
SHOW COLUMNS FROM funding WHERE Field IN ('project_status', 'project_id', 'project_uid');
SHOW COLUMNS FROM membership WHERE Field IN ('rlogx_id', 'member_id', 'ccm_type_code');
SHOW COLUMNS FROM publications WHERE Field IN ('publication_id', 'publication_uid', 'pub_type');

