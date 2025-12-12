# Smoke Test Guide - Budgets Transformation

## Quick Smoke Test

This guide helps you verify the budgets transformation layer works correctly on your server.

## Step 1: Start Your Server

Make sure your server is running:

```bash
# On your server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Step 2: Test Transformation (No Database Write)

Test the transformation layer without writing to the database:

### Option A: Using curl (if server is accessible)

```bash
curl -X POST "http://your-server:8000/admin/uploads/raw-data?write_to_db=false" \
  -F "file=@test_smoke_budgets.csv" | jq .
```

### Option B: Using Python requests script

```bash
python tests/test_budgets_api.py http://your-server:8000
```

### Option C: Using Swagger UI

1. Navigate to `http://your-server:8000/docs`
2. Find `/admin/uploads/raw-data`
3. Click "Try it out"
4. Upload `test_smoke_budgets.csv`
5. Set `write_to_db` to `false`
6. Click "Execute"
7. Review the response

## Step 3: Verify Results

Check the response for:

### ✅ Expected in Response:

```json
{
  "success": true,
  "summary": {
    "total_rows": 3,
    "valid_rows": 3,
    "invalid_rows": 0,
    "preview_data": [
      {
        "grant_number": "GRANT001",
        "grant_start_date": "2020-01-15",
        "project_title": "Smoke Test Project 1",
        ...
      },
      {
        "grant_number": "CORE002",  // ✅ Should be filled from Core Project Number
        "grant_start_date": "2021-01-15",  // ✅ Date format converted
        ...
      },
      {
        "grant_number": "PERIOD003",  // ✅ Should be filled from Period Grant Number
        "grant_start_date": "2022-03-11",  // ✅ Date format converted
        ...
      }
    ]
  }
}
```

### ✅ What to Verify:

1. **Column Names**: All should be in `snake_case` format
   - `project_title` ✅
   - `grant_start_date` ✅
   - `grant_number` ✅
   - `rlogx_uid` ✅

2. **Date Formats**: All dates should be ISO format (YYYY-MM-DD)
   - `grant_start_date`: `2020-01-15`, `2021-01-15`, `2022-03-11` ✅
   - `grant_end_date`: `2024-12-31`, `2025-12-31` ✅

3. **Grant Number Fallback**:
   - Row 1: Has `grant_number: "GRANT001"` (original value) ✅
   - Row 2: Has `grant_number: "CORE002"` (filled from Core Project Number) ✅
   - Row 3: Has `grant_number: "PERIOD003"` (filled from Period Grant Number) ✅

4. **No Errors**: `invalid_rows: 0` and `errors: []` ✅

## Step 4: Test Database Write (Optional - Only After Verification)

Once you're confident transformations work:

1. Set `write_to_db=true` in the request
2. Upload the same test file
3. Verify records appear in your database:

```sql
SELECT * FROM budgets WHERE rlogx_uid LIKE 'SMOKE%' ORDER BY rlogx_uid;
```

4. Check that:
   - All 3 rows are inserted
   - Column names are correct
   - Dates are stored as DATE type
   - Metadata fields are populated (`upload_timestamp`, `source_filename`)

## Troubleshooting

### If you see errors:

- **"Could not auto-detect dataset type"**: Check column names match exactly (case-insensitive)
- **Date parsing errors**: Check date formats in your test file
- **Database connection errors**: Verify database credentials in config

### If transformations look wrong:

- Check the `preview_data` in the response
- Compare column names to expected snake_case format
- Verify date formats are ISO (YYYY-MM-DD)

## Cleanup

After testing, you can remove test records:

```sql
DELETE FROM budgets WHERE rlogx_uid LIKE 'SMOKE%';
```

