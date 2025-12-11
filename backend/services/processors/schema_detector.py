"""
Schema detection for auto-identifying dataset types from column headers.

This module contains the logic to automatically detect which dataset type
a file belongs to based on its column structure.

Column definitions are sourced from the processors themselves to avoid duplication.
"""
import logging
from typing import Optional, Set, Dict
import pandas as pd

logger = logging.getLogger(__name__)


def normalize_column_name(col: str) -> str:
    """
    Normalize column name for comparison.
    
    Args:
        col: Column name
        
    Returns:
        Normalized column name (lowercase, stripped, spaces to underscores)
    """
    return col.lower().strip().replace(" ", "_").replace("-", "_")


def get_dataset_signatures() -> Dict[str, Dict[str, Set[str]]]:
    """
    Get dataset signatures by querying processors for their column definitions.
    
    This ensures column definitions are only defined once (in the processors).
    
    Returns:
        Dictionary mapping dataset_type to {required: set, optional: set}
    """
    # Import here to avoid circular import
    from backend.services.processors.processor_factory import get_processor
    
    signatures = {}
    dataset_types = [
        "rlogx_membership",
        "rlogx_publications",
        "rlogx_budgets",
        "rlogx_funding",
        "proposals",
        "ilabs"
    ]
    
    for dataset_type in dataset_types:
        processor = get_processor(dataset_type)
        if processor:
            required = {normalize_column_name(col) for col in processor.get_required_columns()}
            optional = {normalize_column_name(col) for col in processor.get_optional_columns()}
            signatures[dataset_type] = {
                "required": required,
                "optional": optional
            }
        else:
            logger.warning(f"Processor not found for {dataset_type}, skipping from signatures")
    
    return signatures


def detect_dataset_type(df: pd.DataFrame) -> Optional[str]:
    """
    Auto-detect dataset type from DataFrame columns.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dataset type string if detected, None otherwise
    """
    if df.empty:
        logger.warning("Cannot detect dataset type from empty DataFrame")
        return None
    
    # Get signatures from processors (single source of truth)
    dataset_signatures = get_dataset_signatures()
    
    # Normalize column names
    normalized_columns = {normalize_column_name(col) for col in df.columns}
    
    # Score each dataset type based on how many required columns match
    scores = {}
    for dataset_type, signature in dataset_signatures.items():
        required_normalized = signature["required"]
        
        # Count how many required columns are present
        matches = required_normalized & normalized_columns
        match_ratio = len(matches) / len(required_normalized) if required_normalized else 0
        
        # Only consider if at least 80% of required columns match
        if match_ratio >= 0.8:
            scores[dataset_type] = {
                "match_ratio": match_ratio,
                "matches": len(matches),
                "total_required": len(required_normalized)
            }
    
    if not scores:
        logger.warning(f"Could not detect dataset type. Columns: {list(df.columns)}")
        return None
    
    # Return the dataset type with the highest match ratio
    best_match = max(scores.items(), key=lambda x: x[1]["match_ratio"])
    dataset_type = best_match[0]
    
    logger.info(
        f"Detected dataset type: {dataset_type} "
        f"(match ratio: {best_match[1]['match_ratio']:.2%}, "
        f"{best_match[1]['matches']}/{best_match[1]['total_required']} required columns)"
    )
    
    return dataset_type


def get_expected_columns(dataset_type: str) -> Set[str]:
    """
    Get expected columns for a dataset type by querying the processor.
    
    Args:
        dataset_type: Dataset type identifier
        
    Returns:
        Set of expected column names (normalized)
    """
    # Import here to avoid circular import
    from backend.services.processors.processor_factory import get_processor
    
    processor = get_processor(dataset_type)
    if not processor:
        return set()
    
    required = {normalize_column_name(col) for col in processor.get_required_columns()}
    optional = {normalize_column_name(col) for col in processor.get_optional_columns()}
    return required | optional

