# Testing the Budgets Transformation Layer

This guide explains how to test the RLOGX budgets transformation layer.

## Overview

The transformation layer processes validated data rows and:
1. **Maps column names** from processor format (e.g., `'Grant Start Date'`) to database format (e.g., `'grant_start_date'`)
2. **Parses date columns** and standardizes them to ISO format (YYYY-MM-DD)
3. **Fills missing Grant Number** with fallback values (Core Project Number → Period Grant Number)
4. **Handles missing values** appropriately

## Testing Approaches

### 1. Unit Testing (Direct Code Testing)

Run the unit test script that tests the transformation logic directly:

```bash
# From the project root
python -m pytest tests/test_budgets_transform.py -v

# Or run directly
python tests/test_budgets_transform.py
```

**What it tests:**
- Column name mapping
- Date parsing with various formats
- Grant Number fallback logic
- Missing value handling

**Expected output:**
- Detailed transformation verification
- Sample mappings and date formats
- Fallback logic verification

### 2. API Testing (End-to-End)

Test through the actual API endpoint:

#### Step 1: Start the server

```bash
# Make sure your server is running
uvicorn app:app --reload
```

#### Step 2: Run the API test script

```bash
python tests/test_budgets_api.py

# Or specify a different base URL
python tests/test_budgets_api.py http://localhost:8000
```

#### Step 3: Manual API testing with curl

```bash
# Create a test CSV file (or use your own)
cat > test_budgets.csv << 'EOF'
Project Title,Peer Review Type,Grant Start Date,Grant End Date,RLOGX UID,Import Source,Workspace Status,Last Updated,Grant Number,Core Project Number,Period Grant Number
Test Project,Type A,2020-01-15,2024-12-31,UID001,Source1,Active,2024-01-01,GRANT001,CORE001,PERIOD001
Test Project 2,Type B,01/15/2021,12/31/2025,UID002,Source2,Active,2024-02-01,,CORE002,PERIOD002
EOF

# Upload via API (without writing to database)
curl -X POST "http://localhost:8000/admin/uploads/raw-data?write_to_db=false" \
  -F "file=@test_budgets.csv" | jq .
```

#### Step 4: Check the response

Look for the `preview_data` field in the response. This contains the **transformed rows** with:
- Column names in snake_case format
- Dates in ISO format (YYYY-MM-DD)
- Grant Number filled from fallback values when needed

### 3. Interactive Testing via Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Find the `/admin/uploads/raw-data` endpoint
3. Click "Try it out"
4. Upload a test CSV/Excel file
5. Set `write_to_db` to `false` (to test transformations only)
6. Examine the `preview_data` in the response

## What to Verify

### ✅ Column Name Mapping

Original column names should be mapped to snake_case:
- `'Grant Start Date'` → `'grant_start_date'`
- `'Grant Number'` → `'grant_number'`
- `'RLOGX UID'` → `'rlogx_uid'`
- `'Research Program(s)'` → `'research_programs'`

### ✅ Date Parsing

Date columns should be in ISO format (YYYY-MM-DD):
- `'2020-01-15'` → `'2020-01-15'` ✓
- `'01/15/2021'` → `'2021-01-15'` ✓
- `'2022 Mar 11'` → `'2022-03-11'` ✓
- Empty strings → `None` ✓

Date columns to check:
- `grant_start_date`
- `grant_end_date`
- `period_start_date`
- `period_end_date`
- `last_updated`

### ✅ Grant Number Fallback

When `Grant Number` is missing:
1. **First priority**: Fill with `Core Project Number` if available
2. **Second priority**: Fill with `Period Grant Number` if Core Project Number is not available
3. If both are missing, leave as `None`

### ✅ Missing Value Handling

- Empty strings (`''`) → `None`
- `None` values → `None`
- Valid values → Preserved as-is

## Sample Test Data

You can create a test CSV with these scenarios:

```csv
Project Title,Peer Review Type,Grant Start Date,Grant End Date,RLOGX UID,Import Source,Workspace Status,Last Updated,Grant Number,Core Project Number,Period Grant Number,Period Start Date
Project 1,Type A,2020-01-15,2024-12-31,UID001,Source1,Active,2024-01-01,GRANT001,CORE001,PERIOD001,2020-01-01
Project 2,Type B,01/15/2021,12/31/2025,UID002,Source2,Active,2024-02-01,,CORE002,PERIOD002,2021-01-01
Project 3,Type C,2022 Mar 11,2025-12-31,UID003,Source3,Inactive,,,PERIOD003,2022-01-01
```

**Row 1**: Grant Number present (no fallback needed)
**Row 2**: Grant Number missing, should use Core Project Number
**Row 3**: Grant Number and Core Project Number missing, should use Period Grant Number

## Troubleshooting

### Issue: Dates not parsing correctly

**Check:**
- Date format in source data
- `parse_date()` utility function handles your format
- Check logs for parsing errors

### Issue: Column names not mapping correctly

**Check:**
- Column names match exactly (case-sensitive before mapping)
- `_map_column_names()` handles your column name format
- Check the transformed row keys in preview_data

### Issue: Grant Number fallback not working

**Check:**
- Grant Number is actually empty (not just whitespace)
- Core Project Number or Period Grant Number have valid values
- Check logs for debug messages about fallback

## Next Steps

After verifying transformations work correctly:
1. Implement `write_to_database()` method
2. Test end-to-end with database writes
3. Verify data integrity in database

