"""
Quick script to test database writes for budgets data.
"""
import sys
from pathlib import Path
import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_db_write(base_url="http://localhost:8000"):
    """Test database write functionality."""
    print("=" * 80)
    print("Testing Budgets Database Write")
    print("=" * 80)
    print()
    
    test_file = Path("test_smoke_budgets.csv")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("   Please ensure test_smoke_budgets.csv exists in the current directory")
        return
    
    print(f"Step 1: Uploading {test_file.name} with write_to_db=true...")
    url = f"{base_url}/admin/uploads/raw-data"
    params = {"write_to_db": True}
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'text/csv')}
            response = requests.post(url, files=files, params=params, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('summary', {})
            
            print(f"   ✅ Upload successful!")
            print()
            print(f"Step 2: Results:")
            print(f"   Total rows: {summary.get('total_rows', 0)}")
            print(f"   Valid rows: {summary.get('valid_rows', 0)}")
            print(f"   Invalid rows: {summary.get('invalid_rows', 0)}")
            
            if summary.get('errors'):
                print(f"\n   ⚠️  Errors ({len(summary.get('errors', []))}):")
                for error in summary.get('errors', [])[:5]:
                    print(f"      Row {error.get('row_number')}: {error.get('message')}")
            
            print()
            print(f"Step 3: Database Write Verification")
            print("-" * 80)
            print()
            print("   ✅ If no errors above, check your database:")
            print()
            print("   Run this SQL query to verify records were inserted:")
            print()
            print("   SELECT * FROM budgets WHERE rlogx_uid LIKE 'SMOKE%' ORDER BY rlogx_uid;")
            print()
            print("   Expected: Should see the valid rows (probably 2 rows if one had validation error)")
            print("   - Check that column names are correct (snake_case)")
            print("   - Check that dates are stored as DATE type")
            print("   - Check that upload_timestamp and source_filename are populated")
            print()
            print("   To clean up test data after verification:")
            print("   DELETE FROM budgets WHERE rlogx_uid LIKE 'SMOKE%';")
            
        else:
            print(f"   ❌ Upload failed!")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection error: Could not connect to {base_url}")
        print(f"   Make sure the server is running!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_db_write(base_url)

