#!/usr/bin/env python3
"""Test column name mapping."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.processors.rlogx_funding_processor import RLOGXFundingProcessor

processor = RLOGXFundingProcessor()

# Test CSV column names
test_columns = [
    'projectID', 'projectUID', 'projectTitle', 'projectBegin', 'projectEnd',
    'projectStatusID', 'masterFund', 'trainingProject', 'peerReviewType',
    'peerReviewTypeID', 'importSource', 'grantNumber', 'coreProjectNum',
    'fiscalYear', 'multiPI'
]

print("Column mappings:")
print("-" * 60)
for col in test_columns:
    mapped = processor._map_column_names(col)
    print(f"{col:25} -> {mapped}")

