# SQL Scripts Directory

This directory contains SQL scripts for database schema management and migrations.

## Schema Migration Scripts

### Metadata Columns

- **`add_metadata_columns_all_tables.sql`** - Adds upload metadata columns to all tables at once
  - Tables: `budgets`, `funding`, `ilabs`, `membership`, `proposals`, `publications`
  - Columns: `upload_timestamp`, `source_filename`, `upload_batch_id`, `created_at`
  - Also adds `source_tab_name` for `ilabs` table

- **`add_metadata_columns_individual_tables.sql`** - Individual SQL blocks for each table
  - Allows selective execution per table
  - Same columns as above, organized by table

- **`add_metadata_columns_compatible.sql`** - MySQL/MariaDB compatible version for budgets table
  - Handles existing data with default values
  - Compatible with various MySQL/MariaDB versions

### Missing Columns

- **`add_missing_columns_all.sql`** - Adds missing columns that ORM models expect
  - Funding: `project_status`, `project_id`, `project_uid`
  - Membership: `rlogx_id`, `member_id`, `ccm_type_code`
  - Publications: `publication_id`, `publication_uid`, `pub_type`

- **`check_missing_columns_all.sql`** - Diagnostic script to check which columns are missing

### Column Type Changes

- **`convert_publications_varchar_to_text.sql`** - Converts VARCHAR(255) to TEXT in publications table
  - Fixes MySQL row size limit issues
  - Converts 20+ columns that are likely to have long text content

- **`alter_project_id_to_string.sql`** - Changes `project_id` from INT to VARCHAR(255) in funding table
  - Supports alphanumeric project IDs like "SMOKEFUND001"

### Diagnostic Scripts

- **`check_funding_data.sql`** - Checks what columns exist and what data is in funding table
- **`verify_funding_data.sql`** - Verifies test data was inserted correctly

## Usage

Run SQL scripts directly in your database client (e.g., DBeaver, MySQL Workbench, command line):

```bash
# MySQL command line
mysql -u username -p database_name < sql/add_metadata_columns_all_tables.sql

# Or execute in your database client GUI
```

## Notes

- Scripts are idempotent where possible (will skip if columns already exist)
- Always back up your database before running migration scripts
- Test scripts in a development environment first
- Some scripts may need to be run in specific order (check comments in files)

