#!/usr/bin/env python3
"""
Debug script to check what's happening with funding data writes.
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.services.processors.rlogx_funding_processor import RLOGXFundingProcessor

# Create test data matching the test CSV
test_data = {
    'projectID': ['SMOKEFUND001'],
    'projectUID': ['SMOKEFUNDUID001'],
    'projectTitle': ['Funding Test Project 1'],
    'projectBegin': ['2020-01-15'],
    'projectEnd': ['2024-12-31'],
    'projectStatusID': [1],
    'masterFund': [1],
    'trainingProject': [0],
    'peerReviewType': ['Type A'],
    'peerReviewTypeID': [1],
    'importSource': ['Test Source'],
    'grantNumber': ['GRANT001'],
    'coreProjectNum': ['CORE001'],
    'fiscalYear': [2024],
    'multiPI': [0.5],
}

df = pd.DataFrame(test_data)
print("Original DataFrame columns:")
print(df.columns.tolist())
print()

processor = RLOGXFundingProcessor()

# Validate
valid_rows, errors = processor.validate_dataframe(df)
print(f"Validation: {len(valid_rows)} valid rows, {len(errors)} errors")
if valid_rows:
    print(f"Valid row keys: {list(valid_rows[0].keys())}")
print()

# Transform
transformed_rows = processor.transform_rows(valid_rows)
print(f"Transformation: {len(transformed_rows)} transformed rows")
if transformed_rows:
    print(f"Transformed row keys: {list(transformed_rows[0].keys())}")
    print(f"Transformed row sample:")
    for key, value in list(transformed_rows[0].items())[:10]:
        print(f"  {key}: {value!r}")
print()

# Check column mappings
print("Column mapping examples:")
for col in ['projectID', 'projectUID', 'projectTitle', 'projectBegin', 'projectEnd']:
    mapped = processor._map_column_names(col)
    print(f"  {col} -> {mapped}")

