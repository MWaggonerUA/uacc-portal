-- Convert VARCHAR(255) columns to TEXT in publications table
-- This helps avoid MySQL row size limit (65,535 bytes)
-- TEXT columns don't count toward the row size limit

-- Columns that are likely to contain longer text content
-- Convert these to TEXT to reduce row size:

ALTER TABLE publications MODIFY COLUMN abstract TEXT NULL;
ALTER TABLE publications MODIFY COLUMN affiliations TEXT NULL;
ALTER TABLE publications MODIFY COLUMN authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN title TEXT NULL;
ALTER TABLE publications MODIFY COLUMN grants TEXT NULL;
ALTER TABLE publications MODIFY COLUMN cancer_relevance_justification TEXT NULL;
ALTER TABLE publications MODIFY COLUMN all_ccm_authors_possible_names TEXT NULL;
ALTER TABLE publications MODIFY COLUMN all_ccm_authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN intra_authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN inter_authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN inter_programs TEXT NULL;
ALTER TABLE publications MODIFY COLUMN citation TEXT NULL;
ALTER TABLE publications MODIFY COLUMN cores_used TEXT NULL;
ALTER TABLE publications MODIFY COLUMN research_programs TEXT NULL;
ALTER TABLE publications MODIFY COLUMN research_program TEXT NULL;
ALTER TABLE publications MODIFY COLUMN identified_cancer_centers TEXT NULL;
ALTER TABLE publications MODIFY COLUMN identify_intra_authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN identify_inter_authors TEXT NULL;
ALTER TABLE publications MODIFY COLUMN both_in_trainter TEXT NULL;
ALTER TABLE publications MODIFY COLUMN author_verification TEXT NULL;

-- Now add any missing columns
ALTER TABLE publications ADD COLUMN pub_type VARCHAR(255) NULL;
ALTER TABLE publications ADD COLUMN research_programs TEXT NULL;

