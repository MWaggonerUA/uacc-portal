-- Add missing data columns to budgets table
-- Based on the ORM model, add any columns that don't exist

-- Add research_programs column (this is the one causing your current error)
ALTER TABLE budgets
ADD COLUMN research_programs VARCHAR(255) NULL;

-- Other columns that might be missing (uncomment if needed):
-- ALTER TABLE budgets
-- ADD COLUMN grant_id VARCHAR(255) NULL,
-- ADD COLUMN project_title VARCHAR(255) NULL,
-- ADD COLUMN grant_number VARCHAR(255) NULL,
-- ADD COLUMN core_project_number VARCHAR(255) NULL,
-- ADD COLUMN funding_source VARCHAR(255) NULL,
-- ADD COLUMN peer_review_type VARCHAR(255) NULL,
-- ADD COLUMN grant_start_date DATE NULL,
-- ADD COLUMN grant_end_date DATE NULL,
-- ADD COLUMN grant_direct_cost FLOAT NULL,
-- ADD COLUMN grant_indirect_cost FLOAT NULL,
-- ADD COLUMN grant_total INT NULL,
-- ADD COLUMN prime_award_id VARCHAR(255) NULL,
-- ADD COLUMN prime_agency_name VARCHAR(255) NULL,
-- ADD COLUMN subcontract INT NULL,
-- ADD COLUMN multi_pi FLOAT NULL,
-- ADD COLUMN multi_investigator INT NULL,
-- ADD COLUMN nce INT NULL,
-- ADD COLUMN r01_like INT NULL,
-- ADD COLUMN project_link VARCHAR(255) NULL,
-- ADD COLUMN allocation_of VARCHAR(255) NULL,
-- ADD COLUMN budget_period_id FLOAT NULL,
-- ADD COLUMN period_grant_number VARCHAR(255) NULL,
-- ADD COLUMN period FLOAT NULL,
-- ADD COLUMN period_start_date DATE NULL,
-- ADD COLUMN period_end_date DATE NULL,
-- ADD COLUMN period_directs FLOAT NULL,
-- ADD COLUMN period_indirect FLOAT NULL,
-- ADD COLUMN period_total INT NULL,
-- ADD COLUMN ccsg_fund INT NULL,
-- ADD COLUMN linked_investigators VARCHAR(255) NULL,
-- ADD COLUMN cancer_relevance FLOAT NULL,
-- ADD COLUMN justification VARCHAR(255) NULL,
-- ADD COLUMN rlogx_uid VARCHAR(255) NULL,
-- ADD COLUMN flagged_for_review INT NULL,
-- ADD COLUMN import_source VARCHAR(255) NULL,
-- ADD COLUMN workspace_status VARCHAR(255) NULL,
-- ADD COLUMN imported_pis VARCHAR(255) NULL,
-- ADD COLUMN imported_pi_ids VARCHAR(255) NULL,
-- ADD COLUMN last_updated DATE NULL;

-- Verify the column was added
SHOW COLUMNS FROM budgets LIKE 'research_programs';

