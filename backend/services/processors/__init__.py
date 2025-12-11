"""
Dataset processors package.

Each processor handles a specific dataset type with its own validation,
transformation, and database write logic.
"""
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.processor_factory import get_processor, detect_dataset_type

__all__ = [
    'BaseDatasetProcessor',
    'get_processor',
    'detect_dataset_type'
]

