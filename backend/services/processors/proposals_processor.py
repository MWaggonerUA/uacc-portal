"""
Processor for proposals dataset.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor

logger = logging.getLogger(__name__)


class ProposalsProcessor(BaseDatasetProcessor):
    """Processor for proposals data."""
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for proposals dataset."""
        return [
            'Proposal ID', 'Proposal Title', 'Contact Role Code',
            'Proposal Status', 'Multiple PI Flag', 'Submitted Date',
            'Lead Investigator Name', 'Requested Start Date',
            'Requested End Date', 'Investigator Name', 'Sponsor Name',
            'College Name', 'College Code', 'Total Cost'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for proposals dataset."""
        return [
            'Contact Role Description', 'Proposal Status Description',
            'Lead Investigator Organization Name',
            'Lead Investigator Organization Rollup College Name'
        ]
    
    async def write_to_database(
        self,
        valid_rows: List[Dict[str, Any]],
        db_session: AsyncSession,
        upload_timestamp: str = None
    ) -> int:
        """
        Write proposals data to database.
        
        Multiple files can be uploaded to the same table.
        Each upload is timestamped.
        """
        # TODO: Implement actual database write logic
        # from backend.models.orm_models import ProposalRecord
        # 
        # inserted_count = 0
        # for row in valid_rows:
        #     if upload_timestamp:
        #         row['upload_timestamp'] = upload_timestamp
        #     
        #     db_row = ProposalRecord(**row)
        #     db_session.add(db_row)
        #     inserted_count += 1
        # 
        # await db_session.commit()
        # logger.info(f"Inserted {inserted_count} proposal records (upload: {upload_timestamp})")
        # return inserted_count
        
        logger.warning("Database write not yet implemented for proposals data")
        return len(valid_rows)

