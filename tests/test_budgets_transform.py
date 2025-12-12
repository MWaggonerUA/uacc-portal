"""
Test script for RLOGX budgets transformation layer.

This script tests the transform_rows() method to verify:
- Column name mapping (processor format → database format)
- Date parsing and standardization
- Grant Number fallback logic
- Missing value handling
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from backend.services.processors.rlogx_budgets_processor import RLOGXBudgetsProcessor
from backend.services.processors.utils import parse_date


def create_test_budgets_dataframe():
    """Create a test DataFrame with various scenarios."""
    return pd.DataFrame({
        # Required columns
        'Project Title': ['Test Project 1', 'Test Project 2', 'Test Project 3'],
        'Peer Review Type': ['Type A', 'Type B', 'Type C'],
        'Grant Start Date': ['2020-01-15', '01/15/2021', '2022 Mar 11'],  # Different date formats
        'Grant End Date': ['2024-12-31', '12/31/2025', '2025-12-31'],
        'RLOGX UID': ['UID001', 'UID002', 'UID003'],
        'Import Source': ['Source1', 'Source2', 'Source3'],
        'Workspace Status': ['Active', 'Active', 'Inactive'],
        'Last Updated': ['2024-01-01', '2024-02-01', ''],  # Empty string for testing
        
        # Optional columns with various scenarios
        'Grant Number': ['GRANT001', '', ''],  # Missing Grant Number for rows 2 and 3
        'Core Project Number': ['CORE001', 'CORE002', ''],  # Available for row 2, missing for row 3
        'Period Grant Number': ['PERIOD001', '', 'PERIOD003'],  # Available for row 3 as fallback
        'Grant ID': ['G001', 'G002', 'G003'],
        'Period Start Date': ['2020-01-01', '2021-01-01', '2022-01-01'],
        'Period End Date': ['2020-12-31', '2021-12-31', '2022-12-31'],
        'Grant Direct Cost': [100000.0, 200000.0, 300000.0],
        'Grant Indirect Cost': [50000.0, 100000.0, 150000.0],
        'Research Program(s)': ['Program A', 'Program B', 'Program C'],
    })


def test_transformation():
    """Test the transform_rows method."""
    print("=" * 80)
    print("Testing RLOGX Budgets Transformation Layer")
    print("=" * 80)
    print()
    
    # Create processor
    processor = RLOGXBudgetsProcessor(dataset_type="rlogx_budgets")
    
    # Create test data
    df = create_test_budgets_dataframe()
    print(f"Test DataFrame created with {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print()
    
    # Validate the DataFrame (this will also transform rows in validate_dataframe)
    print("Step 1: Validating DataFrame...")
    valid_rows, errors = processor.validate_dataframe(df)
    
    if errors:
        print(f"  ⚠️  Found {len(errors)} validation errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"    Row {error.row_number}: {error.message}")
        print()
    else:
        print(f"  ✓ Validation passed: {len(valid_rows)} valid rows")
        print()
    
    # Transform rows
    print("Step 2: Transforming rows...")
    transformed_rows = processor.transform_rows(valid_rows)
    print(f"  ✓ Transformed {len(transformed_rows)} rows")
    print()
    
    # Verify transformations
    print("Step 3: Verifying transformations...")
    print("-" * 80)
    
    for i, (original, transformed) in enumerate(zip(valid_rows[:3], transformed_rows[:3])):
        print(f"\nRow {i + 1}:")
        print(f"  Original columns: {sorted(list(original.keys()))[:5]}...")
        print(f"  Transformed columns: {sorted(list(transformed.keys()))[:5]}...")
        
        # Check column name mapping
        print(f"\n  Column Name Mapping:")
        sample_cols = ['Project Title', 'Grant Start Date', 'Grant Number', 'RLOGX UID']
        for col in sample_cols:
            if col in original:
                mapped = processor._map_column_names(col)
                original_val = original.get(col, 'N/A')
                transformed_val = transformed.get(mapped, 'N/A')
                print(f"    '{col}' → '{mapped}'")
                print(f"      Value: {original_val} → {transformed_val}")
        
        # Check date parsing
        print(f"\n  Date Parsing:")
        date_cols = ['Grant Start Date', 'Grant End Date', 'Period Start Date', 'Period End Date', 'Last Updated']
        for col in date_cols:
            if col in original:
                mapped = processor._map_column_names(col)
                original_val = original.get(col, 'N/A')
                transformed_val = transformed.get(mapped, 'N/A')
                print(f"    {col}: '{original_val}' → '{transformed_val}'")
        
        # Check Grant Number fallback
        print(f"\n  Grant Number Fallback Logic:")
        grant_num_orig = original.get('Grant Number', '')
        grant_num_trans = transformed.get('grant_number', '')
        core_proj = original.get('Core Project Number', '')
        period_grant = original.get('Period Grant Number', '')
        
        print(f"    Original Grant Number: '{grant_num_orig}'")
        print(f"    Core Project Number: '{core_proj}'")
        print(f"    Period Grant Number: '{period_grant}'")
        print(f"    Transformed Grant Number: '{grant_num_trans}'")
        
        # Verify fallback logic worked
        if not grant_num_orig or (isinstance(grant_num_orig, str) and grant_num_orig.strip() == ''):
            if core_proj and str(core_proj).strip():
                if grant_num_trans == str(core_proj).strip():
                    print(f"    ✓ Correctly filled from Core Project Number")
                else:
                    print(f"    ✗ Expected '{core_proj}' but got '{grant_num_trans}'")
            elif period_grant and str(period_grant).strip():
                if grant_num_trans == str(period_grant).strip():
                    print(f"    ✓ Correctly filled from Period Grant Number")
                else:
                    print(f"    ✗ Expected '{period_grant}' but got '{grant_num_trans}'")
    
    print()
    print("-" * 80)
    print("\nStep 4: Summary of transformations")
    print("-" * 80)
    
    # Check all column mappings
    print("\nColumn Name Mappings (first transformed row):")
    if transformed_rows:
        original_keys = set(valid_rows[0].keys())
        transformed_keys = set(transformed_rows[0].keys())
        
        print(f"  Original columns: {len(original_keys)}")
        print(f"  Transformed columns: {len(transformed_keys)}")
        
        # Show mapping examples
        print("\n  Sample mappings:")
        sample_cols = ['Project Title', 'Grant Start Date', 'Grant Number', 'RLOGX UID', 
                      'Research Program(s)', 'Core Project Number', 'Period Grant Number']
        for col in sample_cols:
            if col in original_keys:
                mapped = processor._map_column_names(col)
                print(f"    '{col}' → '{mapped}'")
    
    # Verify date format
    print("\nDate Format Verification:")
    date_cols_db = ['grant_start_date', 'grant_end_date', 'period_start_date', 'period_end_date', 'last_updated']
    for date_col in date_cols_db:
        if transformed_rows and date_col in transformed_rows[0]:
            values = [row.get(date_col) for row in transformed_rows if row.get(date_col) is not None]
            if values:
                # Check if dates are in ISO format (YYYY-MM-DD)
                sample = values[0]
                if isinstance(sample, str) and len(sample) == 10 and sample[4] == '-' and sample[7] == '-':
                    print(f"  ✓ {date_col}: ISO format (e.g., '{sample}')")
                elif sample is None:
                    print(f"  ✓ {date_col}: None (optional field)")
                else:
                    print(f"  ⚠️  {date_col}: Unexpected format '{sample}'")
    
    print()
    print("=" * 80)
    print("Transformation test complete!")
    print("=" * 80)


def test_grant_number_fallback():
    """Test Grant Number fallback logic specifically."""
    print("\n" + "=" * 80)
    print("Testing Grant Number Fallback Logic")
    print("=" * 80)
    print()
    
    processor = RLOGXBudgetsProcessor(dataset_type="rlogx_budgets")
    
    test_cases = [
        {
            'name': 'Grant Number present',
            'data': {'Grant Number': 'GRANT001', 'Core Project Number': 'CORE001', 'Period Grant Number': 'PERIOD001'}
        },
        {
            'name': 'Grant Number missing, Core Project Number available',
            'data': {'Grant Number': '', 'Core Project Number': 'CORE002', 'Period Grant Number': 'PERIOD002'}
        },
        {
            'name': 'Grant Number missing, only Period Grant Number available',
            'data': {'Grant Number': None, 'Core Project Number': '', 'Period Grant Number': 'PERIOD003'}
        },
        {
            'name': 'All missing',
            'data': {'Grant Number': '', 'Core Project Number': '', 'Period Grant Number': ''}
        },
        {
            'name': 'Grant Number missing, Core Project Number is number',
            'data': {'Grant Number': None, 'Core Project Number': 12345, 'Period Grant Number': ''}
        },
    ]
    
    for test_case in test_cases:
        print(f"Test Case: {test_case['name']}")
        row = test_case['data'].copy()
        # Add required fields
        row.update({
            'Project Title': 'Test',
            'Peer Review Type': 'Type A',
            'Grant Start Date': '2020-01-01',
            'Grant End Date': '2024-12-31',
            'RLOGX UID': 'UID001',
            'Import Source': 'Source1',
            'Workspace Status': 'Active',
            'Last Updated': '2024-01-01',
        })
        
        # Transform
        transformed = processor.transform_rows([row])
        
        if transformed:
            result = transformed[0]
            grant_num = result.get('grant_number')
            print(f"  Original Grant Number: {row.get('Grant Number')}")
            print(f"  Core Project Number: {row.get('Core Project Number')}")
            print(f"  Period Grant Number: {row.get('Period Grant Number')}")
            print(f"  Result Grant Number: {grant_num}")
            print()


if __name__ == "__main__":
    test_transformation()
    test_grant_number_fallback()

