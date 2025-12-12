"""
Test database writes for all processors (except budgets which was already tested).

This script tests with write_to_db=true to verify data is actually written to the database.
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
    test_files['funding'] = Path("test_db_funding.csv")
    test_files['funding'].write_text(funding_csv)
    
    # Membership test file
    membership_csv = """Member Status,rlogxID,RLOGX UID,Last Name,First Name,Email Address,Date Added to RLOGX,memberID,programName,CCM Start Date,Program End Date,Program Member Type,Program History
Active,1001,SMOKEMEM001,Smith,John,john.smith@example.com,2020-01-15,2001,Program A,2020-01-01,2024-12-31,Member,History A
Active,1002,SMOKEMEM002,Jones,Jane,jane.jones@example.com,2021-02-01,2002,Program B,2021-01-01,2025-12-31,Associate,History B
"""
    test_files['membership'] = Path("test_db_membership.csv")
    test_files['membership'].write_text(membership_csv)
    
    # Publications test file
    publications_csv = """RLOGX Link,publicationID,publicationUID,title,authors,journal,journal_full,pubDate,PubMed Link,pubmeduid
https://rlogx.example.com/pub1,SMOKEPUB001,SMOKEPUBUID001,Test Publication 1,Author A; Author B,Test Journal,Test Journal Full,2020-01-15,https://pubmed.ncbi.nlm.nih.gov/12345,12345
https://rlogx.example.com/pub2,SMOKEPUB002,SMOKEPUBUID002,Test Publication 2,Author C; Author D,Test Journal 2,Test Journal 2 Full,01/15/2021,https://pubmed.ncbi.nlm.nih.gov/67890,67890
"""
    test_files['publications'] = Path("test_db_publications.csv")
    test_files['publications'].write_text(publications_csv)
    
    # Proposals test file
    proposals_csv = """Proposal ID,Proposal Title,Contact Role Code,Proposal Status,Multiple PI Flag,Submitted Date,Lead Investigator Name,Requested Start Date,Requested End Date,Investigator Name,Sponsor Name,College Name,College Code,Total Cost
SMOKEPROP001,Proposal Test 1,CODE1,Status A,Y,2020-01-15,Lead Investigator 1,2021-01-01,2024-12-31,Investigator 1,Sponsor 1,College A,COLA,500000
SMOKEPROP002,Proposal Test 2,CODE2,Status B,N,01/15/2021,Lead Investigator 2,2022-01-01,2025-12-31,Investigator 2,Sponsor 2,College B,COLB,600000
"""
    test_files['proposals'] = Path("test_db_proposals.csv")
    test_files['proposals'].write_text(proposals_csv)
    
    return test_files


def test_processor_db_write(base_url, file_path, dataset_type):
    """Test a single processor with database writes enabled."""
    print(f"\n{'='*80}")
    print(f"Testing {dataset_type.upper()} Processor (with DB write)")
    print('='*80)
    
    url = f"{base_url}/admin/uploads/raw-data"
    params = {"write_to_db": True}  # Enable database writes
    
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
                for error in errors[:3]:
                    print(f"    Row {error.get('row_number')}: {error.get('message')}")
            
            print(f"\n  ✅ Data should now be in the database!")
            print(f"  Check your {dataset_type} table for records with:")
            
            # Print query hints based on dataset type
            if dataset_type == 'funding':
                print(f"    SELECT * FROM funding WHERE project_uid LIKE 'SMOKE%';")
            elif dataset_type == 'membership':
                print(f"    SELECT * FROM membership WHERE rlogx_uid LIKE 'SMOKE%';")
            elif dataset_type == 'publications':
                print(f"    SELECT * FROM publications WHERE publication_uid LIKE 'SMOKE%';")
            elif dataset_type == 'proposals':
                print(f"    SELECT * FROM proposals WHERE proposal_id LIKE 'SMOKE%';")
            
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
    """Run database write tests for all processors."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("="*80)
    print("DATABASE WRITE TESTS FOR ALL PROCESSORS")
    print("="*80)
    print(f"\nAPI Base URL: {base_url}")
    print(f"Write to DB: True (will write to database!)")
    print("\n⚠️  WARNING: This will insert test data into your database!")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    print("\nCreating test files...")
    
    # Create test files
    test_files = create_test_files()
    print(f"  ✅ Created {len(test_files)} test file(s)")
    
    # Test each processor
    results = {}
    processors_to_test = ['funding', 'membership', 'publications', 'proposals']
    
    for dataset_type in processors_to_test:
        if dataset_type in test_files:
            success, valid_rows, invalid_rows = test_processor_db_write(
                base_url, test_files[dataset_type], dataset_type
            )
            results[dataset_type] = {
                'success': success,
                'valid_rows': valid_rows,
                'invalid_rows': invalid_rows
            }
            time.sleep(0.5)
    
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
    print("\nIf all tests passed, check your database with these queries:")
    print("\n  -- Funding")
    print("  SELECT * FROM funding WHERE project_uid LIKE 'SMOKE%';")
    print("\n  -- Membership")
    print("  SELECT * FROM membership WHERE rlogx_uid LIKE 'SMOKE%';")
    print("\n  -- Publications")
    print("  SELECT * FROM publications WHERE publication_uid LIKE 'SMOKE%';")
    print("\n  -- Proposals")
    print("  SELECT * FROM proposals WHERE proposal_id LIKE 'SMOKE%';")
    print("\nTo clean up test data:")
    print("  DELETE FROM funding WHERE project_uid LIKE 'SMOKE%';")
    print("  DELETE FROM membership WHERE rlogx_uid LIKE 'SMOKE%';")
    print("  DELETE FROM publications WHERE publication_uid LIKE 'SMOKE%';")
    print("  DELETE FROM proposals WHERE proposal_id LIKE 'SMOKE%';")
    print("="*80)


if __name__ == "__main__":
    main()

