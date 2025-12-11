"""
Test script for auto-detection and validation.

This script creates sample DataFrames with the actual column names
and tests the auto-detection and validation functionality.
"""
import pandas as pd
from backend.services.processors.schema_detector import detect_dataset_type
from backend.services.processors.processor_factory import get_processor_for_dataframe

# Create sample DataFrames with actual column names
def create_test_dataframes():
    """Create test DataFrames for each dataset type."""
    
    # RLOGX Membership
    membership_df = pd.DataFrame({
        'Internal ID': ['M001', 'M002'],
        'Last Name': ['Smith', 'Jones'],
        'First Name': ['John', 'Jane'],
        'Middle Name': ['A', 'B'],
        'Credentials': ['MD', 'PhD'],
        'Email Address': ['john@example.com', 'jane@example.com'],
        'Author Names': ['John Smith', 'Jane Jones'],
        'programName': ['Program A', 'Program B'],
        'CCSG Role': ['Member', 'Member'],
        'CCM Start Date': ['2020-01-01', '2021-01-01'],
        'CCM End Date': ['2024-12-31', '2025-12-31'],
        'Current Research Program(s)': ['Program A', 'Program B'],
        'Program History': ['History A', 'History B'],
        'Rank (Primary Appointment)': ['Professor', 'Associate'],
        'Department (Primary Appointment)': ['Dept A', 'Dept B'],
        'School (Primary Appointment)': ['School A', 'School B']
    })
    
    # RLOGX Publications
    publications_df = pd.DataFrame({
        'PubMed Link': ['link1', 'link2'],
        'publicationID': ['P001', 'P002'],
        'pubmeduid': ['12345', '67890'],
        'title': ['Title 1', 'Title 2'],
        'authors': ['Author 1', 'Author 2'],
        'journal_full': ['Journal A', 'Journal B'],
        'pmcid': ['PMC1', 'PMC2'],
        'pubDate': ['2023-01-01', '2023-02-01'],
        'abstract': ['Abstract 1', 'Abstract 2'],
        'affiliations': ['Affil 1', 'Affil 2'],
        'grants': ['Grant 1', 'Grant 2'],
        'pubFirstAuthor': ['First 1', 'First 2'],
        'pubLastAuthor': ['Last 1', 'Last 2'],
        'impactValue': [5.0, 6.0],
        'allCCMAuthors_possibleNames': ['Names 1', 'Names 2'],
        'allCCMAuthors': ['Authors 1', 'Authors 2'],
        'researchPrograms': ['Program 1', 'Program 2'],
        'Citation': ['Citation 1', 'Citation 2']
    })
    
    # RLOGX Budgets
    budgets_df = pd.DataFrame({
        'Grant ID': ['G001', 'G002'],
        'Project Title': ['Project 1', 'Project 2'],
        'Grant Number': ['GRANT001', 'GRANT002'],
        'Core Project Number': ['CORE001', 'CORE002'],
        'Funding Source': ['Source 1', 'Source 2'],
        'Peer Review Type': ['Type 1', 'Type 2'],
        'Grant Start Date': ['2020-01-01', '2021-01-01'],
        'Grant End Date': ['2024-12-31', '2025-12-31'],
        'Grant Direct Cost': [100000, 200000],
        'Grant Indirect Cost': [50000, 100000],
        'Grant Total': [150000, 300000],
        'Period Grant Number': ['PERIOD001', 'PERIOD002'],
        'Period Start Date': ['2020-01-01', '2021-01-01'],
        'Period End Date': ['2020-12-31', '2021-12-31'],
        'Period Directs': [10000, 20000],
        'Period Indirect': [5000, 10000],
        'Period Total': [15000, 30000],
        'Linked Investigators': ['Investigator 1', 'Investigator 2'],
        'Research Program(s)': ['Program 1', 'Program 2'],
        'Imported PIs': ['PI 1', 'PI 2']
    })
    
    # RLOGX Funding
    funding_df = pd.DataFrame({
        'projectTitle': ['Project 1', 'Project 2'],
        'grantNumber': ['GRANT001', 'GRANT002'],
        'fundSource': ['Source 1', 'Source 2'],
        'projectBegin': ['2020-01-01', '2021-01-01'],
        'projectEnd': ['2024-12-31', '2025-12-31'],
        'projectSummary': ['Summary 1', 'Summary 2'],
        'indirectCost': [50000, 100000],
        'directCost': [100000, 200000],
        'cancerRelevancePercentage': [80, 90],
        'imported_pi': ['PI 1', 'PI 2'],
        'internalProjectID': ['ID001', 'ID002'],
        'coreProjectNum': ['CORE001', 'CORE002'],
        'peerReviewType': ['Type 1', 'Type 2'],
        'investigators': ['Investigator 1', 'Investigator 2'],
        'Investigators (Principal)': ['PI 1', 'PI 2'],
        'listPrograms': ['Program 1', 'Program 2']
    })
    
    # Proposals
    proposals_df = pd.DataFrame({
        'Proposal ID': ['PROP001', 'PROP002'],
        'Proposal Title': ['Title 1', 'Title 2'],
        'Contact Role Code': ['CODE1', 'CODE2'],
        'Proposal Status': ['Status 1', 'Status 2'],
        'Multiple PI Flag': ['Y', 'N'],
        'Submitted Date': ['2023-01-01', '2023-02-01'],
        'Lead Investigator Name': ['Lead 1', 'Lead 2'],
        'Requested Start Date': ['2024-01-01', '2024-02-01'],
        'Requested End Date': ['2027-12-31', '2028-12-31'],
        'Investigator Name': ['Investigator 1', 'Investigator 2'],
        'Sponsor Name': ['Sponsor 1', 'Sponsor 2'],
        'Total Cost': [500000, 600000]
    })
    
    # iLabs
    ilabs_df = pd.DataFrame({
        'Service ID': ['S001', 'S002'],
        'Service Type': ['Type 1', 'Type 2'],
        'Asset ID': ['A001', 'A002'],
        'Customer Name': ['Customer 1', 'Customer 2'],
        'Customer Lab': ['Lab 1', 'Lab 2'],
        'Customer Department': ['Dept 1', 'Dept 2'],
        'Charge Name': ['Charge 1', 'Charge 2'],
        'Payment Information': ['Payment 1', 'Payment 2'],
        'Expense Object Code|Revenue Object Code': ['CODE1', 'CODE2'],
        'Unit of Measure': ['Unit 1', 'Unit 2'],
        'Completion Date': ['2023-01-01', '2023-02-01'],
        'Core Name': ['Core 1', 'Core 2'],
        'Invoice Num': ['INV001', 'INV002'],
        'Category': ['Category 1', 'Category 2']
    })
    
    return {
        'rlogx_membership': membership_df,
        'rlogx_publications': publications_df,
        'rlogx_budgets': budgets_df,
        'rlogx_funding': funding_df,
        'proposals': proposals_df,
        'ilabs': ilabs_df
    }


def test_auto_detection():
    """Test auto-detection for each dataset type."""
    print("=" * 60)
    print("Testing Auto-Detection")
    print("=" * 60)
    
    test_dfs = create_test_dataframes()
    
    for expected_type, df in test_dfs.items():
        detected_type = detect_dataset_type(df)
        status = "✓" if detected_type == expected_type else "✗"
        print(f"{status} Expected: {expected_type:20} Detected: {detected_type or 'None'}")
        
        if detected_type != expected_type:
            print(f"    Columns in DataFrame: {list(df.columns)[:5]}...")
    
    print()


def test_validation():
    """Test validation for each dataset type."""
    print("=" * 60)
    print("Testing Validation")
    print("=" * 60)
    
    test_dfs = create_test_dataframes()
    
    for dataset_type, df in test_dfs.items():
        processor = get_processor_for_dataframe(df)
        
        if processor:
            print(f"\n{dataset_type}:")
            print(f"  Processor: {processor.__class__.__name__}")
            
            # Test schema validation
            schema_valid, missing_cols = processor.validate_schema(df)
            print(f"  Schema valid: {schema_valid}")
            if not schema_valid:
                print(f"    Missing columns: {missing_cols}")
            
            # Test row validation
            valid_rows, errors = processor.validate_dataframe(df)
            print(f"  Valid rows: {len(valid_rows)}/{len(df)}")
            print(f"  Errors: {len(errors)}")
            
            if errors:
                print(f"    Sample errors:")
                for error in errors[:3]:
                    print(f"      Row {error.row_number}: {error.message}")
        else:
            print(f"\n{dataset_type}: ✗ Processor not found")


if __name__ == "__main__":
    test_auto_detection()
    test_validation()

