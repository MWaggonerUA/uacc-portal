"""
Smoke test script for all processors (except budgets which was already tested).

Tests all processors with write_to_db=false to verify transformations work correctly.
"""
import sys
from pathlib import Path
import requests
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_test_files():
    """Create test CSV files for each dataset type."""
    test_files = {}
    
    # Funding test file
    funding_csv = """projectID,projectUID,projectTitle,projectBegin,projectEnd,projectStatusID,masterFund,trainingProject,peerReviewType,peerReviewTypeID,importSource,grantNumber,coreProjectNum,fiscalYear,multiPI
SMOKEFUND001,SMOKEFUNDUID001,Funding Test Project 1,2020-01-15,2024-12-31,1,1,0,Type A,1,Test Source,GRANT001,CORE001,2024,0.5
SMOKEFUND002,SMOKEFUNDUID002,Funding Test Project 2,01/15/2021,12/31/2025,1,1,1,Type B,2,Test Source,,CORE002,2025,1.0
"""
    test_files['funding'] = Path("test_smoke_funding.csv")
    test_files['funding'].write_text(funding_csv)
    
    # Membership test file
    membership_csv = """Member Status,rlogxID,RLOGX UID,Last Name,First Name,Email Address,Date Added to RLOGX,memberID,programName,CCM Start Date,Program End Date,Program Member Type,Program History
Active,1001,SMOKEMEM001,Smith,John,john.smith@example.com,2020-01-15,2001,Program A,2020-01-01,2024-12-31,Member,History A
Active,1002,SMOKEMEM002,Jones,Jane,jane.jones@example.com,2021-02-01,2002,Program B,2021-01-01,2025-12-31,Associate,History B
"""
    test_files['membership'] = Path("test_smoke_membership.csv")
    test_files['membership'].write_text(membership_csv)
    
    # Publications test file
    publications_csv = """RLOGX Link,publicationID,publicationUID,title,authors,journal,journal_full,pubDate,PubMed Link,pubmeduid
https://rlogx.example.com/pub1,SMOKEPUB001,SMOKEPUBUID001,Test Publication 1,Author A; Author B,Test Journal,Test Journal Full,2020-01-15,https://pubmed.ncbi.nlm.nih.gov/12345,12345
https://rlogx.example.com/pub2,SMOKEPUB002,SMOKEPUBUID002,Test Publication 2,Author C; Author D,Test Journal 2,Test Journal 2 Full,01/15/2021,https://pubmed.ncbi.nlm.nih.gov/67890,67890
"""
    test_files['publications'] = Path("test_smoke_publications.csv")
    test_files['publications'].write_text(publications_csv)
    
    # Proposals test file
    proposals_csv = """Proposal ID,Proposal Title,Contact Role Code,Proposal Status,Multiple PI Flag,Submitted Date,Lead Investigator Name,Requested Start Date,Requested End Date,Investigator Name,Sponsor Name,College Name,College Code,Total Cost
SMOKEPROP001,Proposal Test 1,CODE1,Status A,Y,2020-01-15,Lead Investigator 1,2021-01-01,2024-12-31,Investigator 1,Sponsor 1,College A,COLA,500000
SMOKEPROP002,Proposal Test 2,CODE2,Status B,N,01/15/2021,Lead Investigator 2,2022-01-01,2025-12-31,Investigator 2,Sponsor 2,College B,COLB,600000
"""
    test_files['proposals'] = Path("test_smoke_proposals.csv")
    test_files['proposals'].write_text(proposals_csv)
    
    # iLabs test file
    ilabs_csv = """User Login Email,Charge Name,Status,Billing Status,Quantity,Price,Total Price,Price Type,Creation Date,PI Email,Customer Name,Core Name
user1@example.com,Charge 1,Completed,Billed,1,100.0,100.0,Standard,2020-01-15,pi1@example.com,Customer 1,Core A
user2@example.com,Charge 2,Pending,Unbilled,2,200.0,400.0,Standard,01/15/2021,pi2@example.com,Customer 2,Core B
"""
    test_files['ilabs'] = Path("test_smoke_ilabs.csv")
    test_files['ilabs'].write_text(ilabs_csv)
    
    return test_files


def test_processor(base_url, file_path, dataset_type):
    """Test a single processor."""
    print(f"\n{'='*80}")
    print(f"Testing {dataset_type.upper()} Processor")
    print('='*80)
    
    url = f"{base_url}/admin/uploads/raw-data"
    params = {"write_to_db": False}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/csv')}
            response = requests.post(url, files=files, params=params, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('summary', {})
            
            print(f"  Status: ✅ Success (200)")
            print(f"  Total rows: {summary.get('total_rows', 0)}")
            print(f"  Valid rows: {summary.get('valid_rows', 0)}")
            print(f"  Invalid rows: {summary.get('invalid_rows', 0)}")
            
            errors = summary.get('errors', [])
            if errors:
                print(f"\n  ⚠️  Errors ({len(errors)}):")
                for error in errors[:3]:  # Show first 3
                    print(f"    Row {error.get('row_number')}: {error.get('message')}")
            else:
                print(f"  ✅ No errors")
            
            preview_data = summary.get('preview_data')
            if preview_data:
                print(f"\n  Preview Data:")
                print(f"    Showing {len(preview_data)} row(s)")
                # Show sample of transformed columns
                if preview_data:
                    sample = preview_data[0]
                    sample_cols = list(sample.keys())[:5]
                    print(f"    Sample columns: {', '.join(sample_cols)}")
                    print(f"    All columns in snake_case: ✅" if all('_' in col or col.islower() for col in sample.keys()) else "    ⚠️  Some columns not in snake_case")
                    
                    # Check for date columns (including begin/end columns)
                    date_cols = [col for col in sample.keys() if any(d in col.lower() for d in ['date', 'begin', 'end'])]
                    if date_cols:
                        print(f"    Date columns found: {', '.join(date_cols[:4])}")
                        # Verify date format
                        for date_col in date_cols[:3]:
                            val = sample.get(date_col)
                            if val and isinstance(val, str) and len(val) == 10 and val[4] == '-' and val[7] == '-':
                                print(f"      ✅ {date_col}: ISO format ({val})")
                            elif val:
                                print(f"      ⚠️  {date_col}: May need format check ({val})")
                            elif val is None:
                                print(f"      ℹ️  {date_col}: None (optional field)")
            
            return True, summary.get('valid_rows', 0), summary.get('invalid_rows', 0)
        else:
            print(f"  ❌ Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False, 0, 0
    
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Connection error: Could not connect to {base_url}")
        return False, 0, 0
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, 0, 0


def main():
    """Run smoke tests for all processors."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("="*80)
    print("SMOKE TESTS FOR ALL PROCESSORS")
    print("="*80)
    print(f"\nAPI Base URL: {base_url}")
    print(f"Write to DB: False (transformation testing only)")
    print("\nCreating test files...")
    
    # Create test files
    test_files = create_test_files()
    print(f"  ✅ Created {len(test_files)} test file(s)")
    
    # Test each processor
    results = {}
    
    # Note: iLabs requires Excel file with multiple tabs, so we'll skip it for CSV testing
    processors_to_test = ['funding', 'membership', 'publications', 'proposals']
    
    for dataset_type in processors_to_test:
        if dataset_type in test_files:
            success, valid_rows, invalid_rows = test_processor(
                base_url, test_files[dataset_type], dataset_type
            )
            results[dataset_type] = {
                'success': success,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows
            }
            time.sleep(0.5)  # Small delay between requests
    
    # Cleanup
    print(f"\n{'='*80}")
    print("CLEANUP")
    print('='*80)
    for file_path in test_files.values():
        if file_path.exists():
            file_path.unlink()
            print(f"  ✅ Deleted {file_path.name}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    total_valid = 0
    total_invalid = 0
    all_success = True
    
    for dataset_type, result in results.items():
        status = "✅" if result['success'] and result['invalid_rows'] == 0 else "⚠️"
        print(f"{status} {dataset_type:15} - Valid: {result['valid_rows']:2}, Invalid: {result['invalid_rows']:2}")
        total_valid += result['valid_rows']
        total_invalid += result['invalid_rows']
        if not result['success'] or result['invalid_rows'] > 0:
            all_success = False
    
    print(f"\nTotal: {total_valid} valid rows, {total_invalid} invalid rows")
    
    if all_success:
        print("\n🎉 All processors passed transformation tests!")
    else:
        print("\n⚠️  Some processors had issues - check errors above")
    
    print(f"\nNote: iLabs requires Excel files with multiple tabs, so it was skipped in this CSV test.")
    print("="*80)


if __name__ == "__main__":
    main()

