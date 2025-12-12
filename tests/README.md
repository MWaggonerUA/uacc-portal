# Tests Directory

This directory contains all test scripts for the UACC Portal ETL pipeline.

## Test Scripts

### Integration Tests

- **`run_db_write_tests.py`** - Tests all processors with database writes enabled (`write_to_db=true`)
  - Tests: Funding, Membership, Publications, Proposals
  - Creates test CSV files, uploads them via API, verifies database writes
  - Usage: `python tests/run_db_write_tests.py http://localhost:8000`

- **`run_all_smoke_tests.py`** - Smoke tests for all processors with transformations only (`write_to_db=false`)
  - Tests transformations, validation, column mapping without writing to database
  - Usage: `python tests/run_all_smoke_tests.py http://localhost:8000`

- **`run_db_test.py`** - Quick test for budgets database writes
  - Usage: `python tests/run_db_test.py [base_url]`

### Unit Tests

- **`test_budgets_transform.py`** - Unit tests for budgets transformation logic
  - Tests date parsing, column mapping, grant number fallback logic
  - Usage: `python tests/test_budgets_transform.py`

- **`test_budgets_api.py`** - API integration tests for budgets upload endpoint
  - Tests file upload via FastAPI endpoint
  - Usage: `python tests/test_budgets_api.py [base_url]`

### Debug/Development Scripts

- **`test_column_mapping.py`** - Debug script to test column name mapping
  - Shows how column names are transformed (camelCase → snake_case)
  - Usage: `python tests/test_column_mapping.py`

- **`debug_funding_write.py`** - Debug script to trace funding data transformation
  - Shows step-by-step transformation of funding data
  - Usage: `python tests/debug_funding_write.py`

## Running Tests

All test scripts should be run from the project root directory:

```bash
# From project root
python tests/run_db_write_tests.py http://localhost:8000
python tests/run_all_smoke_tests.py http://localhost:8000
```

## Notes

- Test scripts automatically add the project root to `sys.path` to import backend modules
- Test data is cleaned up automatically after tests complete
- Database write tests will insert test data (prefixed with "SMOKE") that can be cleaned up with the provided SQL queries

