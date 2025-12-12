"""
Test script for testing budgets transformation via API endpoint.

This script demonstrates how to test the transformation layer through the API.
You can use this as a template or run it directly if you have a test server running.
"""
import sys
from pathlib import Path

# Add project root to Python path (if needed for any imports)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json


def create_test_csv():
    """Create a test CSV file for testing."""
    csv_content = """Project Title,Peer Review Type,Grant Start Date,Grant End Date,RLOGX UID,Import Source,Workspace Status,Last Updated,Grant Number,Core Project Number,Period Grant Number,Period Start Date,Period End Date,Grant Direct Cost,Research Program(s)
Test Project 1,Type A,2020-01-15,2024-12-31,UID001,Source1,Active,2024-01-01,GRANT001,CORE001,PERIOD001,2020-01-01,2020-12-31,100000.0,Program A
Test Project 2,Type B,01/15/2021,12/31/2025,UID002,Source2,Active,2024-02-01,,CORE002,PERIOD002,2021-01-01,2021-12-31,200000.0,Program B
Test Project 3,Type C,2022 Mar 11,2025-12-31,UID003,Source3,Inactive,,,PERIOD003,2022-01-01,2022-12-31,300000.0,Program C
"""
    test_file = Path("test_budgets.csv")
    test_file.write_text(csv_content)
    return test_file


def test_api_endpoint(base_url="http://localhost:8000", write_to_db=False):
    """
    Test the upload API endpoint.
    
    Args:
        base_url: Base URL of the API server
        write_to_db: Whether to write to database (default: False for testing transformations only)
    """
    print("=" * 80)
    print("Testing Budgets Transformation via API")
    print("=" * 80)
    print()
    
    # Create test file
    print("Step 1: Creating test CSV file...")
    test_file = create_test_csv()
    print(f"  ✓ Created {test_file}")
    print()
    
    # Upload file
    print(f"Step 2: Uploading file to {base_url}/admin/uploads/raw-data...")
    url = f"{base_url}/admin/uploads/raw-data"
    params = {"write_to_db": write_to_db}
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/csv')}
            response = requests.post(url, files=files, params=params, timeout=30)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Upload successful!")
            print()
            
            # Display results
            print("Step 3: Analyzing results...")
            print("-" * 80)
            
            summary = result.get('summary', {})
            print(f"\nProcessing Summary:")
            print(f"  Total rows: {summary.get('total_rows', 0)}")
            print(f"  Valid rows: {summary.get('valid_rows', 0)}")
            print(f"  Invalid rows: {summary.get('invalid_rows', 0)}")
            print(f"  File name: {summary.get('file_name', 'N/A')}")
            print()
            
            # Show preview data (transformed rows)
            preview_data = summary.get('preview_data')
            if preview_data:
                print(f"Preview Data (Transformed Rows):")
                print(f"  Showing {len(preview_data)} row(s)")
                print()
                
                for i, row in enumerate(preview_data, 1):
                    print(f"  Row {i}:")
                    # Show key transformations
                    print(f"    grant_number: {row.get('grant_number', 'N/A')}")
                    print(f"    grant_start_date: {row.get('grant_start_date', 'N/A')}")
                    print(f"    grant_end_date: {row.get('grant_end_date', 'N/A')}")
                    print(f"    project_title: {row.get('project_title', 'N/A')}")
                    print(f"    rlogx_uid: {row.get('rlogx_uid', 'N/A')}")
                    
                    # Verify column names are snake_case
                    columns = list(row.keys())
                    snake_case_cols = [col for col in columns if '_' in col or col.islower()]
                    print(f"    Column count: {len(columns)} ({len(snake_case_cols)} in snake_case)")
                    print()
                
                # Verify transformations
                print("  Verification:")
                print("    ✓ Column names are in snake_case format")
                
                # Check date formats
                date_cols = ['grant_start_date', 'grant_end_date', 'period_start_date', 'period_end_date']
                for date_col in date_cols:
                    values = [row.get(date_col) for row in preview_data if row.get(date_col)]
                    if values:
                        sample = values[0]
                        if isinstance(sample, str) and len(sample) == 10 and sample[4] == '-' and sample[7] == '-':
                            print(f"    ✓ {date_col}: ISO format (YYYY-MM-DD)")
                        else:
                            print(f"    ⚠️  {date_col}: Format may need attention")
                
                # Check Grant Number fallback
                row2 = preview_data[1] if len(preview_data) > 1 else None
                row3 = preview_data[2] if len(preview_data) > 2 else None
                
                if row2 and row2.get('grant_number'):
                    print(f"    ✓ Row 2 Grant Number filled (should be from Core Project Number)")
                if row3 and row3.get('grant_number'):
                    print(f"    ✓ Row 3 Grant Number filled (should be from Period Grant Number)")
            else:
                print("  No preview data available")
            
            # Show errors if any
            errors = summary.get('errors', [])
            if errors:
                print(f"\n  Errors ({len(errors)}):")
                for error in errors[:5]:  # Show first 5
                    print(f"    Row {error.get('row_number')}: {error.get('message')}")
        else:
            print(f"  ✗ Upload failed!")
            print(f"  Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"  ✗ Connection error: Could not connect to {base_url}")
        print(f"  Make sure the server is running!")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
            print(f"\n  Cleaned up test file: {test_file}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    write_to_db = "--write-db" in sys.argv
    
    print(f"API Base URL: {base_url}")
    print(f"Write to DB: {write_to_db}")
    print()
    
    test_api_endpoint(base_url=base_url, write_to_db=write_to_db)

