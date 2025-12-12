-- Alter project_id column from INT to VARCHAR(255) to support alphanumeric IDs
-- Run this if your database column is still INT type

ALTER TABLE funding MODIFY COLUMN project_id VARCHAR(255) NULL;

