"""
Processor for RLOGX membership dataset.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import MembershipRecord

logger = logging.getLogger(__name__)


class RLOGXMembershipProcessor(BaseDatasetProcessor):
    """Processor for RLOGX membership data."""
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for membership dataset."""
        return [
            'Member Status', 'rlogxID', 'RLOGX UID', 'Last Name', 'First Name',
            'Email Address', 'Date Added to RLOGX', 'memberID', 'programName',
            'CCM Start Date', 'Program End Date', 'Program Member Type',
            'Program History'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for membership dataset."""
        return [
            'NetID', 'Four Year Term', 'Full', 'Associate', 'Internal ID',
            'Middle Name', 'Credentials', 'CCSG Role', 'CCM End Date',
            'Department (Primary Appointment)', 'School (Primary Appointment)',
            'Author Names', 'Current Research Program(s)',
            'Rank (Primary Appointment)'
        ]
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'Date Added to RLOGX',
            'CCM Start Date',
            'Program Start Date',
            'Program End Date',
            'CCM End Date'
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
        Write transformed membership data to database.
        
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
                    'member_status', 'rlogx_id', 'rlogx_uid', 'internal_id',
                    'last_name', 'first_name', 'middle_name', 'credentials',
                    'preferred_name', 'maiden_name', 'salutation', 'suffix',
                    'email_address', 'address', 'phone', 'mobile', 'fax',
                    'orcid', 'author_names', 'date_added_to_rlogx', 'member_id',
                    'ccm_type_code', 'program_name', 'research_interests', 'campus',
                    'race', 'ethnicity', 'gender', 'nih_reporter_id', 'phone_number',
                    'fax_number', 'ccsg_role', 'nih_bibliography_url', 'ccm_start_date',
                    'ccm_end_date', 'current_research_programs', 'program_start_date',
                    'program_end_date', 'program_member_type', 'senior_leadership_title',
                    'program_history', 'rank_primary_appointment', 'department_primary_appointment',
                    'division_primary_appointment', 'school_primary_appointment',
                    'rank_secondary_appointment', 'department_secondary_appointment',
                    'division_secondary_appointment', 'school_secondary_appointment',
                    'themes', 'net_id', 'four_year_term', 'full', 'associate',
                    'last_first_name'
                }
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        # Convert date strings to date objects if needed
                        if key in ('date_added_to_rlogx', 'ccm_start_date', 'ccm_end_date',
                                  'program_start_date', 'program_end_date'):
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
                db_record = MembershipRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} membership record(s) "
                f"(source: {source_filename or 'unknown'}, timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting membership records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

