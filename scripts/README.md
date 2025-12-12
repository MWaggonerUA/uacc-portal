# Scripts Directory

This directory contains utility scripts for database management and maintenance.

## Database Schema Scripts

### Column Management

- **`sync_orm_columns.py`** - Automatically syncs database schema with ORM models
  - Compares ORM model definitions with actual database tables
  - Adds missing columns automatically
  - Usage: `python scripts/sync_orm_columns.py`

- **`add_missing_columns.py`** - Adds specific missing columns to database tables
  - Adds: `project_status`, `project_id`, `project_uid`, `rlogx_id`, `member_id`, `publication_id`, `publication_uid`, `pub_type`
  - Usage: `python scripts/add_missing_columns.py`

- **`convert_publications_to_text.py`** - Converts VARCHAR columns to TEXT in publications table
  - Fixes MySQL row size limit (65,535 bytes) by converting large VARCHAR columns to TEXT
  - Adds missing `pub_type` and `research_programs` columns
  - Usage: `python scripts/convert_publications_to_text.py`

## Usage

All scripts should be run from the project root directory:

```bash
# From project root
python scripts/sync_orm_columns.py
python scripts/add_missing_columns.py
python scripts/convert_publications_to_text.py
```

## Notes

- Scripts automatically add the project root to `sys.path` to import backend modules
- Scripts use the database connection from `backend.services.db`
- Scripts will skip columns that already exist (safe to run multiple times)

