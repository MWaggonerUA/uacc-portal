"""
Processor for iLabs dataset.

iLabs data comes in a single Excel file with multiple tabs.
Each tab should be processed separately.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor
from backend.services.processors.utils import parse_date
from backend.models.orm_models import ILabsRecord

logger = logging.getLogger(__name__)


class ILabsProcessor(BaseDatasetProcessor):
    """Processor for iLabs data (Excel file with multiple tabs)."""
    
    def __init__(self, dataset_type: str = "ilabs"):
        """Initialize processor with dataset type."""
        super().__init__(dataset_type)
        self.current_sheet_name: str = None
    
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
    
    def extract_billing_core(self, sheet_name: str) -> str:
        """
        Extract billing core abbreviation from sheet name.
        
        Extracts the first word from the sheet name, which is typically
        the billing core abbreviation (e.g., "ACSR", "FCIMSR").
        
        Examples:
            "ACSR iLab charge data" -> "ACSR"
            "FCIMSR iLab charge data" -> "FCIMSR"
        
        Args:
            sheet_name: Name of the Excel sheet
            
        Returns:
            Billing core abbreviation, or "Unknown" if sheet name is empty
        """
        if not sheet_name:
            return "Unknown"
        
        # Split by space and take the first part
        parts = sheet_name.strip().split()
        if parts:
            return parts[0]
        else:
            return "Unknown"
    
    def set_sheet_name(self, sheet_name: str):
        """
        Set the current sheet name for billing core extraction.
        
        This should be called before processing each tab so that
        transform_rows() can extract the billing core abbreviation.
        
        Args:
            sheet_name: Name of the current Excel sheet being processed
        """
        self.current_sheet_name = sheet_name
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Performs the following transformations:
        - Maps column names from processor format to database format (snake_case)
        - Standardizes date formats for date columns
        - Extracts billing core abbreviation from sheet name and adds 'billing_core' column
        - Handles missing values appropriately
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        transformed_rows = []
        
        # Date columns that need parsing
        date_columns = [
            'Creation Date',
            'Purchase Date',
            'Completed Date',
            'Billing Date',
            'Date file sent to ERP',
            'Billing Event End Date'
        ]
        
        # Extract billing core from current sheet name
        billing_core = "Unknown"
        if self.current_sheet_name:
            billing_core = self.extract_billing_core(self.current_sheet_name)
            self.logger.debug(f"Extracted billing core '{billing_core}' from sheet name '{self.current_sheet_name}'")
        else:
            self.logger.warning("No sheet name set for billing core extraction")
        
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
            
            # Add billing_core column to each row
            transformed_row['billing_core'] = billing_core
            
            transformed_rows.append(transformed_row)
        
        self.logger.debug(f"Transformed {len(transformed_rows)} rows for database insertion")
        return transformed_rows
    
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
        upload_timestamp: str = None,
        source_filename: str = None,
        upload_batch_id: str = None,
        source_tab_name: str = None
    ) -> int:
        """
        Write transformed iLabs data to database.
        
        Args:
            valid_rows: List of transformed row dictionaries (already mapped to database column names)
            db_session: Database session
            upload_timestamp: ISO format timestamp of the upload
            source_filename: Name of the uploaded file
            upload_batch_id: Optional batch ID for grouping related uploads
            source_tab_name: Name of the Excel tab (for iLabs multi-tab files)
            
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
                    'source_tab_name': source_tab_name or self.current_sheet_name,
                    'upload_batch_id': upload_batch_id,
                }
                
                # Add data fields, only including those that match ORM model attributes
                valid_model_attrs = {
                    'user_login_email', 'pi_email', 'financial_contact_email',
                    'service_id', 'service_type', 'asset_id', 'customer_name',
                    'customer_title', 'customer_lab', 'customer_department',
                    'customer_institute', 'charge_name', 'notes', 'payment_information',
                    'custom_field', 'expense_object_code_revenue_object_code',
                    'account_subaccount', 'orgin_code', 'status', 'billing_status',
                    'unit_of_measure', 'quantity', 'price', 'conversion',
                    'updated_quantity', 'total_price', 'price_type', 'creation_date',
                    'purchase_date', 'completion_date', 'billing_date',
                    'date_file_sent_to_erp', 'billing_event_end_date', 'created_by',
                    'core_name', 'invoice_num', 'no_charge_justification',
                    'ad_hoc_charge_justification', 'organization_name',
                    'company_organization_name', 'charge_id', 'reviewed', 'center',
                    'category', 'usage_type', 'vendor', 'unspsc_code', 'unspsc_name',
                    'facility_catalog_number', 'central_catalog_number', 'core_id',
                    'ck_fund_type', 'final_status', 'billing_core'
                }
                
                for key, value in row.items():
                    if key in valid_model_attrs:
                        # Convert date strings to datetime objects if needed
                        if key in ('creation_date', 'purchase_date', 'completion_date',
                                  'billing_date', 'date_file_sent_to_erp', 'billing_event_end_date'):
                            if value is None:
                                record_data[key] = None
                            elif isinstance(value, str):
                                try:
                                    # Try parsing as datetime first (may have time component)
                                    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    record_data[key] = parsed
                                except (ValueError, AttributeError):
                                    try:
                                        # Try parsing as date only
                                        record_data[key] = datetime.fromisoformat(value).date()
                                    except (ValueError, AttributeError):
                                        self.logger.warning(f"Could not parse date '{value}' for column '{key}', setting to None")
                                        record_data[key] = None
                            else:
                                record_data[key] = value
                        else:
                            record_data[key] = value
                
                # Create and add ORM record
                db_record = ILabsRecord(**record_data)
                db_session.add(db_record)
                inserted_count += 1
            
            # Commit all records
            await db_session.commit()
            self.logger.info(
                f"Successfully inserted {inserted_count} iLabs record(s) "
                f"(source: {source_filename or 'unknown'}, tab: {source_tab_name or self.current_sheet_name or 'unknown'}, "
                f"timestamp: {upload_timestamp})"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error inserting iLabs records: {e}",
                exc_info=True
            )
            await db_session.rollback()
            raise
        
        return inserted_count

