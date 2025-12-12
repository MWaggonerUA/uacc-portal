-- Add upload metadata columns to all tables
-- Run this SQL on your database to add the missing columns to all tables
-- 
-- Compatible with MySQL 5.6+ and MariaDB

-- ============================================================================
-- FUNDING TABLE
-- ============================================================================
ALTER TABLE funding
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

UPDATE funding 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

ALTER TABLE funding
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_funding_upload_timestamp ON funding(upload_timestamp);

-- ============================================================================
-- ILABS TABLE (has extra source_tab_name column)
-- ============================================================================
ALTER TABLE ilabs
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN source_tab_name VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

UPDATE ilabs 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

ALTER TABLE ilabs
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_ilabs_upload_timestamp ON ilabs(upload_timestamp);
CREATE INDEX idx_ilabs_source_tab_name ON ilabs(source_tab_name);

-- ============================================================================
-- MEMBERSHIP TABLE
-- ============================================================================
ALTER TABLE membership
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

UPDATE membership 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

ALTER TABLE membership
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_membership_upload_timestamp ON membership(upload_timestamp);

-- ============================================================================
-- PROPOSALS TABLE
-- ============================================================================
ALTER TABLE proposals
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

UPDATE proposals 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

ALTER TABLE proposals
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_proposals_upload_timestamp ON proposals(upload_timestamp);

-- ============================================================================
-- PUBLICATIONS TABLE
-- ============================================================================
ALTER TABLE publications
ADD COLUMN upload_timestamp DATETIME NULL,
ADD COLUMN source_filename VARCHAR(255) NULL,
ADD COLUMN upload_batch_id VARCHAR(255) NULL,
ADD COLUMN created_at DATETIME NULL;

UPDATE publications 
SET 
    upload_timestamp = NOW(),
    source_filename = 'legacy_import',
    created_at = NOW()
WHERE upload_timestamp IS NULL;

ALTER TABLE publications
MODIFY COLUMN upload_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
MODIFY COLUMN source_filename VARCHAR(255) NOT NULL DEFAULT 'unknown',
MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_publications_upload_timestamp ON publications(upload_timestamp);

-- ============================================================================
-- VERIFY ALL TABLES
-- ============================================================================
SHOW COLUMNS FROM funding LIKE 'upload%';
SHOW COLUMNS FROM ilabs LIKE 'upload%';
SHOW COLUMNS FROM membership LIKE 'upload%';
SHOW COLUMNS FROM proposals LIKE 'upload%';
SHOW COLUMNS FROM publications LIKE 'upload%';

