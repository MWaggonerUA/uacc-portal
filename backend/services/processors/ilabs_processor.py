"""
Processor for iLabs dataset.

iLabs data comes in a single Excel file with multiple tabs.
Each tab should be processed separately.
"""
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor

logger = logging.getLogger(__name__)


class ILabsProcessor(BaseDatasetProcessor):
    """Processor for iLabs data (Excel file with multiple tabs)."""
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for iLabs dataset."""
        return [
            'User Login Email', 'Charge Name', 'Status', 'Billing Status',
            'Quantity', 'Price', 'Total Price',
            'Price Type', 'Creation Date'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for iLabs dataset."""
        return [
            'Date file sent to ERP', 'PI Email', 'Billing Event End Date',
            'Customer Department', 'Payment Information',
            'Expense Object Code|Revenue Object Code', 'Core Name', 'Category',
            'Service ID', 'Service Type', 'Asset ID', 'Customer Name',
            'Customer Lab', 'Conversion', 'Updated Quantity',
            'Created By', 'Invoice Num', 'Charge ID'
        ]
    
    def parse_excel_tabs(self, file_path: str) -> List[Tuple[str, pd.DataFrame]]:
        """
        Parse all tabs from an Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of tuples (tab_name, DataFrame)
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            tabs = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                if not df.empty:
                    tabs.append((sheet_name, df))
                    logger.info(f"Parsed tab '{sheet_name}': {len(df)} rows")
            return tabs
        except Exception as e:
            logger.error(f"Error parsing Excel tabs: {e}")
            raise
    
    async def write_to_database(
        self,
        valid_rows: List[Dict[str, Any]],
        db_session: AsyncSession,
        upload_timestamp: str = None
    ) -> int:
        """
        Write iLabs data to database.
        
        Each tab is processed separately and timestamped.
        """
        # TODO: Implement actual database write logic
        # from backend.models.orm_models import ILabsRecord
        # 
        # inserted_count = 0
        # for row in valid_rows:
        #     if upload_timestamp:
        #         row['upload_timestamp'] = upload_timestamp
        #     
        #     db_row = ILabsRecord(**row)
        #     db_session.add(db_row)
        #     inserted_count += 1
        # 
        # await db_session.commit()
        # logger.info(f"Inserted {inserted_count} iLabs records (upload: {upload_timestamp})")
        # return inserted_count
        
        logger.warning("Database write not yet implemented for iLabs data")
        return len(valid_rows)

