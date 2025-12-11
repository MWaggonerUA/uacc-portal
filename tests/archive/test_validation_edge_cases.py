"""
Test edge cases for validation: missing columns, empty rows, etc.
"""
import pandas as pd
from backend.services.processors.processor_factory import get_processor_for_dataframe

def test_missing_required_columns():
    """Test detection when required columns are missing."""
    print("=" * 60)
    print("Testing Missing Required Columns")
    print("=" * 60)
    
    # Create a DataFrame with only some required columns
    df = pd.DataFrame({
        'Internal ID': ['M001'],
        'Last Name': ['Smith'],
        'First Name': ['John'],
        # Missing many required columns
    })
    
    detected = get_processor_for_dataframe(df)
    if detected:
        print(f"✗ Should not detect processor, but got: {detected.dataset_type}")
    else:
        print("✓ Correctly did not detect processor (insufficient columns)")
    print()


def test_empty_rows():
    """Test validation with empty rows."""
    print("=" * 60)
    print("Testing Empty Rows")
    print("=" * 60)
    
    # Create membership DataFrame with one empty row
    df = pd.DataFrame({
        'Internal ID': ['M001', None],
        'Last Name': ['Smith', None],
        'First Name': ['John', None],
        'Middle Name': ['A', None],
        'Credentials': ['MD', None],
        'Email Address': ['john@example.com', None],
        'Author Names': ['John Smith', None],
        'programName': ['Program A', None],
        'CCSG Role': ['Member', None],
        'CCM Start Date': ['2020-01-01', None],
        'CCM End Date': ['2024-12-31', None],
        'Current Research Program(s)': ['Program A', None],
        'Program History': ['History A', None],
        'Rank (Primary Appointment)': ['Professor', None],
        'Department (Primary Appointment)': ['Dept A', None],
        'School (Primary Appointment)': ['School A', None]
    })
    
    processor = get_processor_for_dataframe(df)
    if processor:
        valid_rows, errors = processor.validate_dataframe(df)
        print(f"Valid rows: {len(valid_rows)}/{len(df)}")
        print(f"Errors: {len(errors)}")
        if errors:
            print(f"  Sample error: {errors[0].message}")
    print()


def test_partial_match():
    """Test detection with partial column match (should still work if 80% match)."""
    print("=" * 60)
    print("Testing Partial Match (80% threshold)")
    print("=" * 60)
    
    # Create membership DataFrame missing 2 out of 16 required columns (87.5% match)
    df = pd.DataFrame({
        'Internal ID': ['M001'],
        'Last Name': ['Smith'],
        'First Name': ['John'],
        'Middle Name': ['A'],
        'Credentials': ['MD'],
        'Email Address': ['john@example.com'],
        'Author Names': ['John Smith'],
        'programName': ['Program A'],
        'CCSG Role': ['Member'],
        'CCM Start Date': ['2020-01-01'],
        'CCM End Date': ['2024-12-31'],
        'Current Research Program(s)': ['Program A'],
        'Program History': ['History A'],
        'Rank (Primary Appointment)': ['Professor'],
        # Missing: 'Department (Primary Appointment)', 'School (Primary Appointment)'
    })
    
    from backend.services.processors.schema_detector import detect_dataset_type
    detected = detect_dataset_type(df)
    if detected == 'rlogx_membership':
        print(f"✓ Correctly detected {detected} with 14/16 required columns (87.5% match)")
    else:
        print(f"✗ Expected rlogx_membership, got {detected}")
    print()


if __name__ == "__main__":
    test_missing_required_columns()
    test_empty_rows()
    test_partial_match()

