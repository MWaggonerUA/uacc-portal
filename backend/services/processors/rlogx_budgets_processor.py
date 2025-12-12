"""
Processor for RLOGX budgets dataset.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import BudgetRecord

logger = logging.getLogger(__name__)


class RLOGXBudgetsProcessor(BaseDatasetProcessor):
    """Processor for RLOGX budgets data."""
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for budgets dataset."""
        return [
            'Project Title', 'Peer Review Type', 'Grant Start Date',
            'Grant End Date', 'RLOGX UID', 'Import Source',
            'Workspace Status', 'Last Updated'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for budgets dataset."""
        return [
            'Subcontract', 'Multi PI', 'Multi Investigator', 'NCE', 'R01 Like',
            'Grant ID', 'Grant Number', 'Core Project Number',
            'Funding Source', 'Grant Direct Cost', 'Grant Indirect Cost',
            'Grant Total', 'Period Grant Number', 'Period Start Date',
            'Period End Date', 'Period Directs', 'Period Indirect', 'Period Total',
            'Linked Investigators', 'Research Program(s)', 'Imported PIs'
        ]
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Fills missing 'Grant Number' with 'Core Project Number' (first priority) 
          or 'Period Grant Number' (second priority)
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'Grant Start Date',
            'Grant End Date',
            'Period Start Date',
            'Period End Date',
            'Last Updated'
        ]
        
        for row in valid_rows:
            # First, check if Grant Number is missing and fill with fallback values if needed
            grant_number = row.get('Grant Number')
            core_project_num = row.get('Core Project Number')
            period_grant_number = row.get('Period Grant Number')
            
            # Check if Grant Number is missing (None, empty string, or whitespace)
            is_grant_number_missing = (
                grant_number is None or 
                (isinstance(grant_number, str) and grant_number.strip() == '')
            )
            
            # If Grant Number is missing, try to fill it
            if is_grant_number_missing:
                # Check if Core Project Number has a valid value (not None and not empty string)
                has_core_project_num = (
                    core_project_num is not None and
                    (
                        (isinstance(core_project_num, str) and core_project_num.strip()) or
                        not isinstance(core_project_num, str)
                    )
                )
                
                # Check if Period Grant Number has a valid value (not None and not empty string)
                has_period_grant_num = (
                    period_grant_number is not None and
                    (
                        (isinstance(period_grant_number, str) and period_grant_number.strip()) or
                        not isinstance(period_grant_number, str)
                    )
                )
                
                # First priority: Core Project Number
                if has_core_project_num:
                    if isinstance(core_project_num, str):
                        row['Grant Number'] = core_project_num
                    else:
                        # Handle non-string values (e.g., numbers)
                        row['Grant Number'] = str(core_project_num).strip()
                    self.logger.debug(
                        f"Filled missing Grant Number with Core Project Number: '{core_project_num}'"
                    )
                # Second priority: Period Grant Number (if Core Project Number not available)
                elif has_period_grant_num:
                    if isinstance(period_grant_number, str):
                        row['Grant Number'] = period_grant_number
                    else:
                        # Handle non-string values (e.g., numbers)
                        row['Grant Number'] = str(period_grant_number).strip()
                    self.logger.debug(
                        f"Filled missing Grant Number with Period Grant Number: '{period_grant_number}'"
                    )
            
            transformed_row = {}
            
            # Map all column names and transform values
            for col_name, value in row.items():
                # Map column name to database format (snake_case)
                db_col_name = self._map_column_names(col_name)
                
                # Parse date columns
                if col_name in date_columns:
                    transformed_row[db_col_name] = parse_date(value)
                else:
                    # For non-date columns, preserve the value (already validated)
                    # Convert NaN/None to None for database compatibility
                    if value is None or (isinstance(value, str) and value.strip() == ''):
                        transformed_row[db_col_name] = None
                    else:
                        transformed_row[db_col_name] = value
            
            transformed_rows.append(transformed_row)
        
        self.logger.debug(f"Transformed {len(transformed_rows)} rows for database insertion")
        return transformed_rows
    
    async def write_to_database(
        self,
        valid_rows: List[Dict[str, Any]],
        db_session: AsyncSession,
        upload_timestamp: str = None,
        source_filename: str = None,
        upload_batch_id: str = None
    ) -> int:
        """
        Write transformed budgets data to database.
        
        Args:
            valid_rows: List of transformed row dictionaries (already mapped to database column names)
            db_session: Database session
            upload_timestamp: ISO format timestamp of the upload
            source_filename: Name of the uploaded file
            upload_batch_id: Optional batch ID for grouping related uploads
            
        Returns:
            Number of rows successfully inserted
        """
        if not valid_rows:
            self.logger.warning("No valid rows to insert")
            return 0
        
        # Parse upload_timestamp if it's a string
        if upload_timestamp:
            try:
                if isinstance(upload_timestamp, str):
                    upload_dt = datetime.fromisoformat(upload_timestamp.replace('Z', '+00:00'))
                else:
                    upload_dt = upload_timestamp
            except (ValueError, AttributeError):
                self.logger.warning(f"Could not parse upload_timestamp '{upload_timestamp}', using current time")
                upload_dt = datetime.now()
        else:
            upload_dt = datetime.now()
        
        inserted_count = 0
        
        try:
            for row in valid_rows:
                # Create database record, filtering out keys that don't match ORM model columns
                # Only include fields that exist in the BudgetRecord model
                record_data = {
                    'upload_timestamp': upload_dt,
                    'source_filename': source_filename or 'unknown',
                    'upload_batch_id': upload_batch_id,
                }
                
                # Add data fields, only including those that match ORM model attributes
                valid_model_attrs = {
                    'grant_id', 'project_title', 'grant_number', 'core_project_number',
                    'funding_source', 'peer_review_type', 'grant_start_date', 'grant_end_date',
                    'grant_direct_cost', 'grant_indirect_cost', 'grant_total',
                    'prime_award_id', 'prime_agency_name', 'subcontract', 'multi_pi',
                    'multi_investigator', 'nce', 'r01_like', 'project_link', 'allocation_of',
                    'budget_period_id', 'period_grant_number', 'period', 'period_start_date',
                    'period_end_date', 'period_directs', 'period_indirect', 'period_total',
                    'ccsg_fund', 'linked_investigators', 'research_programs', 'cancer_relevance',
                    'justification', 'rlogx_uid', 'flagged_for_review', 'import_source',
                    'workspace_status', 'imported_pis', 'imported_pi_ids', 'last_updated'
                }
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        # Convert date strings to date objects if needed
                        if key in ('grant_start_date', 'grant_end_date', 'period_start_date', 
                                  'period_end_date', 'last_updated'):
                            if value is None:
                                record_data[key] = None
                            elif isinstance(value, str):
                                try:
                                    # Parse ISO format date string (YYYY-MM-DD)
                                    record_data[key] = datetime.fromisoformat(value).date()
                                except (ValueError, AttributeError):
                                    # If parsing fails, keep as None
                                    self.logger.warning(f"Could not parse date '{value}' for column '{key}', setting to None")
                                    record_data[key] = None
                            else:
                                # Already a date/datetime object or other type
                                record_data[key] = value
                        else:
                            record_data[key] = value
                
                # Create and add ORM record
                db_record = BudgetRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} budget record(s) "
                f"(source: {source_filename or 'unknown'}, timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting budget records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

