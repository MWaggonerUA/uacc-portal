"""
Processor for proposals dataset.
"""
import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import ProposalRecord

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
    
    def _normalize_yes_no(self, value: Any) -> int:
        """
        Normalize yes/no values to 1/0.
        
        Handles various formats:
        - "yes"/"no", "Yes"/"No", "YES"/"NO" → 1/0
        - Already coded 1/0 → 1/0
        - Missing/empty values → 0
        
        Args:
            value: Value to normalize
            
        Returns:
            1 if value explicitly indicates "yes", 0 otherwise (including missing values)
        """
        if value is None:
            return 0
        
        # Handle string values
        if isinstance(value, str):
            value = value.strip().lower()
            if not value or value in ('', 'nan', 'none', 'null', 'n/a', 'na'):
                return 0
            # Check for explicit yes values
            if value in ('yes', 'y', '1', 'true', 't'):
                return 1
            # Check for explicit no values
            if value in ('no', 'n', '0', 'false', 'f'):
                return 0
            # For unknown string values, default to 0 (conservative approach)
            return 0
        
        # Handle numeric values
        if isinstance(value, (int, float)):
            # Check for NaN
            if isinstance(value, float) and math.isnan(value):
                return 0
            # Convert to int: 1 if non-zero, 0 if zero
            return 1 if int(value) != 0 else 0
        
        # Handle boolean values
        if isinstance(value, bool):
            return 1 if value else 0
        
        # For any other type, default to 0
        return 0
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Converts yes/no columns to 1/0
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'Submitted Date',
            'Requested Start Date',
            'Requested End Date'
        ]
        
        # Yes/no columns that need to be converted to 1/0
        yes_no_columns = [
            'Multiple PI Flag'
        ]
        
        for row in valid_rows:
            transformed_row = {}
            
            # Map all column names and transform values
            for col_name, value in row.items():
                # Map column name to database format (snake_case)
                db_col_name = self._map_column_names(col_name)
                
                # Parse date columns
                if col_name in date_columns:
                    transformed_row[db_col_name] = parse_date(value)
                # Convert yes/no columns to 1/0
                elif col_name in yes_no_columns:
                    transformed_row[db_col_name] = self._normalize_yes_no(value)
                else:
                    # For non-date, non-yes/no columns, preserve the value (already validated)
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
        Write transformed proposals data to database.
        
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
                # Create database record
                record_data = {
                    'upload_timestamp': upload_dt,
                    'source_filename': source_filename or 'unknown',
                    'upload_batch_id': upload_batch_id,
                }
                
                # Add data fields, only including those that match ORM model attributes
                valid_model_attrs = {
                    'proposal_id', 'proposal_title', 'contact_role_description',
                    'contact_role_code', 'total_effort', 'proposal_status',
                    'proposal_status_description', 'multiple_pi_flag', 'submitted_date',
                    'lead_investigator_organization_name', 'lead_investigator_organization_code',
                    'lead_investigator_name', 'requested_start_date', 'requested_end_date',
                    'total_cost_by_investigator', 'f_a_revenue_percentage_by_investigator_organization',
                    'total_cost_by_investigator1', 'indirect_cost_by_investigator_organization',
                    'direct_cost_by_investigator_organization',
                    'indirect_cost_by_investigator_organization1', 'investigator_name',
                    'organization_name', 'organization_code', 'sponsor_name',
                    'lead_investigator_organization_rollup_college_name', 'college_name',
                    'college_code', 'college_name1', 'college_code1', 'total_cost'
                }
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        # Convert date strings to date objects if needed
                        if key in ('submitted_date', 'requested_start_date', 'requested_end_date'):
                            if value is None:
                                record_data[key] = None
                            elif isinstance(value, str):
                                try:
                                    record_data[key] = datetime.fromisoformat(value).date()
                                except (ValueError, AttributeError):
                                    self.logger.warning(f"Could not parse date '{value}' for column '{key}', setting to None")
                                    record_data[key] = None
                            else:
                                record_data[key] = value
                        else:
                            record_data[key] = value
                
                # Create and add ORM record
                db_record = ProposalRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} proposal record(s) "
                f"(source: {source_filename or 'unknown'}, timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting proposal records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

