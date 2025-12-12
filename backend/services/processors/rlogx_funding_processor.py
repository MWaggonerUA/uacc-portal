"""
Processor for RLOGX funding dataset.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import FundingRecord

logger = logging.getLogger(__name__)


class RLOGXFundingProcessor(BaseDatasetProcessor):
    """Processor for RLOGX funding data."""
    
    def get_required_columns(self) -> List[str]:
        """Return required columns for funding dataset."""
        return [
            'projectID', 'projectUID', 'projectTitle', 'projectBegin',
            'projectEnd', 'projectStatusID', 'masterFund', 'trainingProject',
            'peerReviewType', 'peerReviewTypeID', 'importSource'
        ]
    
    def get_optional_columns(self) -> List[str]:
        """Return optional columns for funding dataset."""
        return [
            'fiscalYear', 'isSubContract', 'multiPI', 'multiInvestigator',
            'noCostExt', 'R01_like', 'isCCSGFund', 'imported_pi', 'investigators',
            'Investigators (Principal)', 'listPrograms', 'grantNumber',
            'projectSummary', 'indirectCost', 'directCost', 'fundSource',
            'cancerRelevancePercentage', 'internalProjectID', 'coreProjectNum'
        ]
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Fills missing 'grantNumber' with 'coreProjectNum' value
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'projectBegin',
            'projectEnd',
            'projectTS'
        ]
        
        for row in valid_rows:
            # First, check if grantNumber is missing and fill with coreProjectNum if needed
            grant_number = row.get('grantNumber')
            core_project_num = row.get('coreProjectNum')
            
            # Check if grantNumber is missing (None, empty string, or whitespace)
            is_grant_number_missing = (
                grant_number is None or 
                (isinstance(grant_number, str) and grant_number.strip() == '')
            )
            
            # If grantNumber is missing and coreProjectNum has a value, use it
            if is_grant_number_missing and core_project_num is not None:
                if isinstance(core_project_num, str) and core_project_num.strip():
                    row['grantNumber'] = core_project_num
                    self.logger.debug(
                        f"Filled missing grantNumber with coreProjectNum value: '{core_project_num}'"
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
        Write transformed funding data to database.
        
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
                record_data = {
                    'upload_timestamp': upload_dt,
                    'source_filename': source_filename or 'unknown',
                    'upload_batch_id': upload_batch_id,
                }
                
                # Add data fields, only including those that match ORM model attributes
                valid_model_attrs = {
                    'project_status', 'project_id', 'project_uid', 'fund_ws_id',
                    'fiscal_year', 'project_title', 'grant_number', 'fund_source',
                    'project_begin', 'project_end', 'project_status_id', 'project_summary',
                    'master_fund', 'allocation_of', 'training_project', 'indirect_cost',
                    'direct_cost', 'cancer_relevance_percentage', 'peer_review_type_id',
                    'fund_review_status_id', 'batch_id', 'import_source', 'import_file',
                    'imported_pi', 'imported_pi_id', 'project_ts', 'is_subcontract',
                    'multi_pi', 'multi_investigator', 'no_cost_ext', 'r01_like',
                    'is_ccsg_fund', 'prime_award_id', 'prime_agency_name', 'funding_ic',
                    'restricted_funds', 'internal_project_id', 'project_sort', 'copied_from',
                    'inv_cancer_relevance_percentage', 'inv_justification', 'inv_notes',
                    'inv_verified_by', 'inv_verified_ts', 'orig_project_id', 'is_core',
                    'flag_for_review', 'core_project_num', 'project_url', 'is_supplement',
                    'include_in_roi', 'view_budget_begin', 'view_budget_end', 'unobligated_balance',
                    'fund_code', 'grant_type', 'grant_activity', 'is_clinical_trial',
                    'grant_purpose', 'public_health_relevance', 'modified_date', 'modified_by',
                    'peer_review_type', 'investigators', 'investigators_principal', 'member_types',
                    'total_allocs', 'list_programs', 'this_count', 'investigators_other',
                    'total_budgets', 'subcontract_in_direct_cost', 'subcontract_in_indirect_cost',
                    'subcontract_out_direct_cost', 'subcontract_out_indirect_cost'
                }
                
                matched_keys = []
                unmatched_keys = []
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        matched_keys.append(key)
                        # Convert date strings to date objects if needed
                        # Note: dates should already be date objects from transform_rows, but handle both cases
                        if key in ('project_begin', 'project_end'):
                            if value is None:
                                record_data[key] = None
                            elif isinstance(value, str):
                                try:
                                    record_data[key] = datetime.fromisoformat(value).date()
                                except (ValueError, AttributeError):
                                    self.logger.warning(f"Could not parse date '{value}' for column '{key}', setting to None")
                                    record_data[key] = None
                            elif hasattr(value, 'date'):  # Already a date object
                                record_data[key] = value
                            else:
                                record_data[key] = value
                        else:
                            record_data[key] = value
                    else:
                        unmatched_keys.append(key)
                
                # Log first row to help debug column mapping issues
                if inserted_count == 0:
                    self.logger.info(f"First row - Matched keys: {matched_keys[:10]}{'...' if len(matched_keys) > 10 else ''}")
                    if unmatched_keys:
                        self.logger.warning(f"First row - Unmatched keys (will be skipped): {unmatched_keys[:10]}{'...' if len(unmatched_keys) > 10 else ''}")
                    if len(matched_keys) == 0:
                        self.logger.error("No keys matched! All data fields will be NULL. Check column name mapping.")
                
                # Create and add ORM record
                db_record = FundingRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} funding record(s) "
                f"(source: {source_filename or 'unknown'}, timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting funding records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

