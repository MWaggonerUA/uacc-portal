"""
Base dataset processor class.

All dataset-specific processors inherit from this class and implement
dataset-specific validation, transformation, and database write logic.
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.upload_models import UploadError

logger = logging.getLogger(__name__)


class BaseDatasetProcessor(ABC):
    """
    Base class for dataset processors.
    
    Each dataset type (RLOGX membership, publications, budgets, funding,
    proposals, iLabs) should have its own processor class that inherits
    from this base class.
    """
    
    def __init__(self, dataset_type: str):
        """
        Initialize processor.
        
        Args:
            dataset_type: Name/identifier of the dataset type
        """
        self.dataset_type = dataset_type
        self.logger = logging.getLogger(f"{__name__}.{dataset_type}")
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """
        Return list of required column names for this dataset type.
        
        Returns:
            List of required column names
        """
        pass
    
    @abstractmethod
    def get_optional_columns(self) -> List[str]:
        """
        Return list of optional column names for this dataset type.
        
        Returns:
            List of optional column names
        """
        pass
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that the DataFrame has the required columns.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_columns)
        """
        required = self.get_required_columns()
        # Create case-insensitive mapping of actual columns
        actual_columns_lower = {str(col).strip().lower(): col for col in df.columns}
        required_lower = {col.lower().strip(): col for col in required}
        
        # Check which required columns are missing (case-insensitive)
        missing = []
        for req_col_lower, req_col_original in required_lower.items():
            if req_col_lower not in actual_columns_lower:
                missing.append(req_col_original)  # Use original case for error message
        
        if missing:
            return False, missing
        return True, []
    
    def validate_row(self, row: pd.Series, row_number: int) -> List[UploadError]:
        """
        Validate a single row of data.
        
        Override this method in subclasses for dataset-specific validation.
        
        Args:
            row: pandas Series representing a row
            row_number: Row number (1-indexed, accounting for header)
            
        Returns:
            List of UploadError objects (empty if row is valid)
        """
        errors = []
        
        # Basic validation: check required columns are not null
        # Create a case-insensitive mapping of row index (strip whitespace too)
        row_index_lower = {str(col).strip().lower(): col for col in row.index}
        
        required = self.get_required_columns()
        for col in required:
            col_normalized = col.strip().lower()
            # Try exact match first, then case-insensitive
            if col in row.index:
                col_key = col
            elif col_normalized in row_index_lower:
                col_key = row_index_lower[col_normalized]
            else:
                # Column not found - this should have been caught in schema validation
                # But if it wasn't, skip it to avoid errors
                continue
            
            value = row[col_key]
            if pd.isna(value) or (isinstance(value, str) and str(value).strip() == ""):
                errors.append(UploadError(
                    row_number=row_number,
                    column=col,
                    message=f"Required column '{col}' is empty",
                    value=None
                ))
        
        return errors
    
    def transform_row(self, row: pd.Series) -> Dict[str, Any]:
        """
        Transform a row to match database schema.
        
        Override this method in subclasses for dataset-specific transformations.
        Default implementation just converts to dict and handles NaN values.
        
        Args:
            row: pandas Series representing a row
            
        Returns:
            Dictionary ready for database insertion
        """
        row_dict = row.to_dict()
        
        # Convert NaN to None for database compatibility
        for key, value in row_dict.items():
            if pd.isna(value):
                row_dict[key] = None
            elif isinstance(value, str):
                row_dict[key] = value.strip()
        
        return row_dict
    
    def _map_column_names(self, column_name: str) -> str:
        """
        Convert processor column names to database column names (snake_case).
        
        Converts column names with spaces, camelCase, mixed case, and special characters
        to snake_case format suitable for database column names.
        
        Handles:
        - Spaces: 'Project Title' → 'project_title'
        - camelCase: 'rlogxID' → 'rlogx_id', 'projectID' → 'project_id'
        - Mixed case: 'RLOGX UID' → 'rlogx_uid'
        - Parentheses: 'Research Program(s)' → 'research_programs', 'Rank (Primary Appointment)' → 'rank_primary_appointment'
        - Special characters: 'F&A' → 'f_a', 'Expense Object Code|Revenue Object Code' → 'expense_object_code_revenue_object_code'
        - Hyphens: 'Ad-hoc' → 'ad_hoc'
        - Multiple capitals: 'allCCMAuthors' → 'all_ccm_authors'
        - Already snake_case: 'pub_date' → 'pub_date'
        
        Examples:
            'Project Title' → 'project_title'
            'RLOGX UID' → 'rlogx_uid'
            'Grant Start Date' → 'grant_start_date'
            'rlogxID' → 'rlogx_id'
            'memberID' → 'member_id'
            'publicationID' → 'publication_id'
            'Research Program(s)' → 'research_programs'
            'Rank (Primary Appointment)' → 'rank_primary_appointment'
            'F&A Revenue Percentage' → 'f_a_revenue_percentage'
            'Expense Object Code|Revenue Object Code' → 'expense_object_code_revenue_object_code'
            'Ad-hoc Charge Justification' → 'ad_hoc_charge_justification'
            'allCCMAuthors' → 'all_ccm_authors'
        
        Args:
            column_name: Original column name (may contain spaces, camelCase, mixed case, special chars)
            
        Returns:
            Column name in snake_case format
        """
        if not column_name:
            return column_name
        
        # Convert to string and strip whitespace
        name = str(column_name).strip()
        
        # Handle special parentheses patterns first
        # '(s)' is a plural indicator - replace with 's' directly
        # 'Research Program(s)' → 'Research Programs' → 'research_programs'
        name = re.sub(r'\(s\)', 's', name, flags=re.IGNORECASE)
        
        # Handle other parentheses: replace with space to keep content
        # 'Rank (Primary Appointment)' → 'Rank Primary Appointment' → 'rank_primary_appointment'
        name = re.sub(r'[()]', ' ', name)
        
        # Replace special characters with underscores before processing
        # Handle hyphens, pipes, ampersands, and other non-alphanumeric chars (except underscores)
        name = re.sub(r'[^\w\s]', '_', name)  # Replace non-word, non-space chars with underscore
        
        # Replace spaces and other whitespace with underscores
        name = '_'.join(name.split())
        
        # Handle sequences of multiple capital letters followed by lowercase
        # This handles cases like 'allCCMAuthors' → 'all_CCM_Authors'
        # Pattern: lowercase/digit, then 2+ capitals, then capital+lowercase
        name = re.sub(r'(?<=[a-z0-9_])([A-Z]{2,})(?=[A-Z][a-z])', r'_\1_', name)
        
        # Handle camelCase: insert underscore before capital letters that follow lowercase or digits
        # This handles cases like:
        # - 'rlogxID' → 'rlogx_ID' → 'rlogx_id'
        # - 'subcontract_in_directCost' → 'subcontract_in_direct_Cost' → 'subcontract_in_direct_cost'
        # - 'fundWSID' → 'fund_WSID' → but we need special handling for all-caps sequences
        name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name)
        
        # Handle all-caps abbreviations that should be split
        # 'fundWSID' → 'fund_WSID' → we need 'fund_WS_ID'
        # Pattern: word boundary before 2+ capitals at end or before another capital+lowercase
        # Actually, let's handle sequences of 2+ capitals that aren't already separated
        # 'WSID' should become 'WS_ID' if followed by nothing or underscore, but 'WS' if part of a word
        # For 'fundWSID', we want 'fund_WS_ID'
        # Let's insert underscore between consecutive capitals where the second starts a new "word"
        # This is tricky - let's handle it by looking for patterns like XXXX where we want X_XX or XX_XX
        # Actually, for abbreviations like 'WSID', 'CCM', we might want to keep them together
        # But 'fundWSID' should be 'fund_WS_ID' based on the expected output
        # Handle all-caps abbreviations: only split if they follow lowercase (camelCase context)
        # 'fundWSID' → 'fund_WSID' → 'fund_WS_ID' (split because it follows lowercase)
        # 'RLOGX UID' → 'RLOGX_UID' stays together (standalone acronym, no split)
        # Pattern: lowercase/underscore, then exactly 4 capitals → split into 2+2
        # This only splits abbreviations that are part of camelCase, not standalone words
        name = re.sub(r'(?<=[a-z_])([A-Z]{2})([A-Z]{2})(?![A-Za-z])', r'\1_\2', name)
        
        # Handle sequences of multiple capital letters followed by lowercase
        # This ensures 'CCMAuthors' becomes 'CCM_Authors' (then lowercase makes it 'ccm_authors')
        # But we need to be careful not to break single capitals at word boundaries
        # Actually, the above regex should handle this, but let's also handle cases where
        # we have multiple capitals in a row that should be treated as one unit
        # For example: 'CCM' should stay together, but 'CCMAuthors' should become 'CCM_Authors'
        # The regex above should handle this correctly
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove any consecutive underscores
        while '__' in name:
            name = name.replace('__', '_')
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before database insertion.
        
        Override in subclasses for dataset-specific transformations:
        - Date format standardization
        - Missing value filling
        - Computed columns
        - Column name mapping (processor names → database names)
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries ready for database insertion
        """
        return valid_rows
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[UploadError]]:
        """
        Validate entire DataFrame and return valid rows and errors.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (valid_rows, errors)
        """
        valid_rows = []
        errors = []
        
        # Filter out unnamed columns (pandas sometimes creates these from Excel files)
        # Also filter out columns that are completely empty (all NaN)
        unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        
        cols_to_drop = list(set(unnamed_cols + empty_cols))
        if cols_to_drop:
            self.logger.warning(
                f"Found {len(cols_to_drop)} column(s) to filter out "
                f"(unnamed: {len(unnamed_cols)}, empty: {len(empty_cols)}): {cols_to_drop[:5]}"
            )
            df = df.drop(columns=cols_to_drop)
        
        # Filter out completely empty rows and non-data rows BEFORE validation
        # A row is considered non-data if:
        # 1. All values are NaN or empty strings, OR
        # 2. It has no values in any expected columns (required + optional)
        original_row_count = len(df)
        
        # Preserve original index for accurate row number reporting
        # Store original index as a column temporarily
        df = df.copy()
        df['_original_index'] = df.index
        
        # Get expected columns (required + optional) for this dataset
        # Use case-insensitive matching since column names might vary
        expected_cols = self.get_required_columns() + self.get_optional_columns()
        expected_cols_lower = {col.lower().strip() for col in expected_cols}
        
        # Create case-insensitive mapping of actual columns to expected columns
        actual_to_expected = {}
        for col in df.columns:
            if col != '_original_index':
                col_lower = str(col).strip().lower()
                if col_lower in expected_cols_lower:
                    actual_to_expected[col] = True
        
        # Create a mask for rows that should be filtered out
        def is_non_data_row(row):
            # Exclude the _original_index column from the check
            data_cols = [col for col in df.columns if col != '_original_index']
            data_row = row[data_cols]
            
            # Check 1: Is the row completely empty (all NaN or empty strings)?
            row_str = data_row.astype(str).str.strip()
            if (row_str == '').all() or data_row.isna().all():
                return True
            
            # Check 2: Count how many columns have actual data (non-empty, non-NaN)
            non_empty_count = 0
            for col in data_cols:
                value = row[col]
                if pd.notna(value) and str(value).strip() != '':
                    non_empty_count += 1
            
            # Filter out rows with very few columns with data (likely message rows)
            # Require at least 3 columns with data to be considered a valid data row
            # This catches rows like those with only messages in column AV
            if non_empty_count < 3:
                return True
            
            # Check 3: If we have expected columns defined, also check if row has data in expected columns
            if expected_cols:
                has_expected_data = False
                for col in data_cols:
                    if col in actual_to_expected:
                        value = row[col]
                        # Check if value is not empty/NaN
                        if pd.notna(value) and str(value).strip() != '':
                            has_expected_data = True
                            break
                
                # If no expected columns have data, this is not a data row
                return not has_expected_data
            
            # Row has enough data columns to be considered valid
            return False
        
        non_data_row_mask = df.apply(is_non_data_row, axis=1)
        non_data_row_count = non_data_row_mask.sum()
        
        if non_data_row_count > 0:
            self.logger.info(
                f"Filtering out {non_data_row_count} non-data rows "
                f"(empty or no values in expected columns) out of {original_row_count} total"
            )
            df = df[~non_data_row_mask].copy()
        
        # First, validate schema (before removing _original_index)
        schema_valid, missing_cols = self.validate_schema(df.drop(columns=['_original_index'], errors='ignore'))
        if not schema_valid:
            self.logger.error(f"Schema validation failed. Missing columns: {missing_cols}")
            # Add schema errors for all rows with original row numbers
            for _, row in df.iterrows():
                original_idx = row['_original_index']
                errors.append(UploadError(
                    row_number=int(original_idx) + 2,  # +2 for header row
                    column=None,
                    message=f"Missing required columns: {', '.join(missing_cols)}",
                    value=None
                ))
            return valid_rows, errors
        
        # Remove the temporary _original_index column for validation
        original_indices = df['_original_index'].values
        df = df.drop(columns=['_original_index'])
        
        # Validate each row
        for df_idx, (idx, row) in enumerate(df.iterrows()):
            # Use the preserved original index for row number reporting
            original_idx = original_indices[df_idx]
            row_number = int(original_idx) + 2  # +2 because idx is 0-based and we assume header row
            
            # Validate row
            row_errors = self.validate_row(row, row_number)
            if row_errors:
                errors.extend(row_errors)
                continue
            
            # Transform and add to valid rows
            try:
                transformed_row = self.transform_row(row)
                valid_rows.append(transformed_row)
            except Exception as e:
                self.logger.error(f"Error transforming row {row_number}: {e}")
                errors.append(UploadError(
                    row_number=row_number,
                    message=f"Error transforming row: {str(e)}",
                    value=None
                ))
        
        self.logger.info(f"Validated {len(df)} rows: {len(valid_rows)} valid, {len(errors)} errors")
        return valid_rows, errors
    
    @abstractmethod
    async def write_to_database(
        self,
        valid_rows: List[Dict[str, Any]],
        db_session: AsyncSession,
        upload_timestamp: str = None
    ) -> int:
        """
        Write validated rows to the appropriate database table.
        
        Args:
            valid_rows: List of validated and transformed row dictionaries
            db_session: Database session
            upload_timestamp: Timestamp of the upload (for tracking)
            
        Returns:
            Number of rows successfully inserted
        """
        pass
    
    def get_table_name(self) -> str:
        """
        Return the database table name for this dataset type.
        
        Override in subclasses if needed.
        """
        return self.dataset_type.lower().replace(" ", "_")

