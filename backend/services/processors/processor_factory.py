"""
Processor factory for routing to the correct dataset processor.

This module provides a factory function to get the appropriate processor
for a given dataset type.
"""
import logging
from typing import Optional
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.schema_detector import detect_dataset_type

logger = logging.getLogger(__name__)

# Registry of processors (will be populated when processors are imported)
_processor_registry: dict[str, type[BaseDatasetProcessor]] = {}


def register_processor(dataset_type: str, processor_class: type[BaseDatasetProcessor]):
    """
    Register a processor class for a dataset type.
    
    Args:
        dataset_type: Dataset type identifier
        processor_class: Processor class (not instance)
    """
    _processor_registry[dataset_type] = processor_class
    logger.debug(f"Registered processor for dataset type: {dataset_type}")


def get_processor(dataset_type: str) -> Optional[BaseDatasetProcessor]:
    """
    Get a processor instance for the given dataset type.
    
    Args:
        dataset_type: Dataset type identifier
        
    Returns:
        Processor instance or None if not found
    """
    if dataset_type not in _processor_registry:
        logger.error(f"No processor registered for dataset type: {dataset_type}")
        return None
    
    processor_class = _processor_registry[dataset_type]
    return processor_class(dataset_type)


def get_processor_for_dataframe(df) -> Optional[BaseDatasetProcessor]:
    """
    Auto-detect dataset type and get appropriate processor.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Processor instance or None if detection fails
    """
    dataset_type = detect_dataset_type(df)
    if not dataset_type:
        return None
    
    return get_processor(dataset_type)


# Import all processors to register them
# This will be done when the processors are created
def _register_all_processors():
    """Register all available processors."""
    try:
        from backend.services.processors.rlogx_membership_processor import RLOGXMembershipProcessor
        register_processor("rlogx_membership", RLOGXMembershipProcessor)
    except ImportError:
        logger.debug("RLOGX membership processor not yet implemented")
    
    try:
        from backend.services.processors.rlogx_publications_processor import RLOGXPublicationsProcessor
        register_processor("rlogx_publications", RLOGXPublicationsProcessor)
    except ImportError:
        logger.debug("RLOGX publications processor not yet implemented")
    
    try:
        from backend.services.processors.rlogx_budgets_processor import RLOGXBudgetsProcessor
        register_processor("rlogx_budgets", RLOGXBudgetsProcessor)
    except ImportError:
        logger.debug("RLOGX budgets processor not yet implemented")
    
    try:
        from backend.services.processors.rlogx_funding_processor import RLOGXFundingProcessor
        register_processor("rlogx_funding", RLOGXFundingProcessor)
    except ImportError:
        logger.debug("RLOGX funding processor not yet implemented")
    
    try:
        from backend.services.processors.proposals_processor import ProposalsProcessor
        register_processor("proposals", ProposalsProcessor)
    except ImportError:
        logger.debug("Proposals processor not yet implemented")
    
    try:
        from backend.services.processors.ilabs_processor import ILabsProcessor
        register_processor("ilabs", ILabsProcessor)
    except ImportError:
        logger.debug("iLabs processor not yet implemented")


# Auto-register processors on import
_register_all_processors()

