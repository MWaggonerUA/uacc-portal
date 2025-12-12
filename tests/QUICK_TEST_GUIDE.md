# Quick Testing Guide for Budgets Transformation

## Quick Start

### Option 1: Direct Code Testing (Fastest)

```bash
# From project root directory
python tests/test_budgets_transform.py

# Or run as a module (alternative)
python -m tests.test_budgets_transform

# If you get import errors, set PYTHONPATH:
PYTHONPATH=. python tests/test_budgets_transform.py
```

This will test the transformation logic directly without needing a running server.

### Option 2: API Testing (Most Realistic)

1. **Start your server:**
   ```bash
   uvicorn app:app --reload
   ```

2. **In another terminal, run:**
   ```bash
   python tests/test_budgets_api.py
   ```

   Or use curl:
   ```bash
   curl -X POST "http://localhost:8000/admin/uploads/raw-data?write_to_db=false" \
     -F "file=@test_budgets.csv" | jq .summary.preview_data
   ```

### Option 3: Interactive Testing

1. Go to `http://localhost:8000/docs`
2. Find `/admin/uploads/raw-data`
3. Upload a test file with `write_to_db=false`
4. Check the `preview_data` field in the response

## What to Look For

✅ **Column names should be snake_case**: `grant_start_date`, `grant_number`, etc.  
✅ **Dates should be ISO format**: `2020-01-15` (not `01/15/2020` or `2020 Jan 15`)  
✅ **Grant Number fallback works**: Empty Grant Number → fills from Core Project Number or Period Grant Number  
✅ **Empty values become None**: Empty strings (`''`) → `None`

## Sample Test CSV

Save this as `test_budgets.csv`:

```csv
Project Title,Peer Review Type,Grant Start Date,Grant End Date,RLOGX UID,Import Source,Workspace Status,Last Updated,Grant Number,Core Project Number,Period Grant Number
Test Project,Type A,2020-01-15,2024-12-31,UID001,Source1,Active,2024-01-01,GRANT001,CORE001,PERIOD001
Test Project 2,Type B,01/15/2021,12/31/2025,UID002,Source2,Active,2024-02-01,,CORE002,PERIOD002
Test Project 3,Type C,2022 Mar 11,2025-12-31,UID003,Source3,Inactive,,,PERIOD003
```

**Expected transformations:**
- Row 2: `grant_number` should be `"CORE002"` (from Core Project Number)
- Row 3: `grant_number` should be `"PERIOD003"` (from Period Grant Number)
- All dates in ISO format: `2020-01-15`, `2021-01-15`, `2022-03-11`

