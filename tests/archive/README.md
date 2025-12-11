# Test Files Archive

This directory contains test scripts used during development to verify auto-detection and validation functionality.

## Files

- `test_auto_detection.py` - Tests auto-detection of all 6 dataset types
- `test_validation_edge_cases.py` - Tests edge cases (missing columns, empty rows, partial matches)

## Usage

To run these tests:

```bash
source .venv/bin/activate
python3 tests/archive/test_auto_detection.py
python3 tests/archive/test_validation_edge_cases.py
```

## Status

All tests passed successfully. The auto-detection and validation systems are working correctly.

