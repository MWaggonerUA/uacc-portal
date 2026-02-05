"""
Processor for Banner Billings dataset (Clinical Trials).

Banner Billings data comes in Excel files with multiple tabs.
Each tab represents one bill with data both inside and outside
the main table section.

Workbook filename indicates invoice type: "Hospital" or "Professional"
(e.g. "AZCC May 2025 Banner Hospital Invoices.xlsx"). The two types
are similar but require slightly different extraction handling.

Dates in workbook names (e.g. "May 2025", "September 2025", "Sept 2025")
are parsed and stored as invoice_date (first of month, YYYY-MM-DD).
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.processors.base_processor import BaseDatasetProcessor

logger = logging.getLogger(__name__)

# Invoice types derived from workbook filename
INVOICE_TYPE_HOSPITAL = "hospital"
INVOICE_TYPE_PROFESSIONAL = "professional"
INVOICE_TYPE_UNKNOWN = "unknown"

# Target columns to extract (same for both invoice types)
TARGET_COLUMNS = ["Charge Amount", "Adjustment", "Balance Due"]

# Text that indicates we've passed the data table (totals/footer)
TABLE_END_MARKERS = ["TOTAL AMOUNT DUE", "BALANCE THIS STATEMENT"]

# Hospital: single header row. Professional: 2-row header (some merged cells)
HOSPITAL_HEADER_ROWS = 1
PROFESSIONAL_HEADER_ROWS = 2

# Metadata fields to extract (above the table). Hospital: labels in B, values in C.
# Professional: labels in A, values in B. Missing fields left blank.
METADATA_FIELDS_HOSPITAL = ["PI", "STUDY NAME", "IRB NO", "KFS NO"]  # PI optional
METADATA_FIELDS_PROFESSIONAL = ["PI", "STUDY NAME", "STUDY CODE", "IRB NO", "KFS NO"]  # IRB NO optional

# Month name patterns for parsing date from workbook filename (order: longer first)
_MONTH_TO_NUM = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_INVOICE_DATE_PATTERN = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"sept|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})",
    re.IGNORECASE
)


class BannerBillingsProcessor(BaseDatasetProcessor):
    """
    Processor for Banner Billings data (Excel file with multiple tabs).
    
    Each tab contains one bill with:
    - Header/metadata information outside the main table
    - A table section with line item details
    
    This processor extracts both the metadata and table data from each tab.
    """
    
    def __init__(self, dataset_type: str = "banner_billings"):
        """Initialize processor with dataset type."""
        super().__init__(dataset_type)
        self.current_sheet_name: Optional[str] = None
        self.current_workbook_name: Optional[str] = None
        self.current_invoice_type: str = INVOICE_TYPE_UNKNOWN  # hospital | professional
        self.current_invoice_date: str = ""  # YYYY-MM-01 or blank if not found
    
    def get_required_columns(self) -> List[str]:
        """
        Return required columns for Banner Billings dataset.
        
        STUB: These are placeholder columns. Update once sample data is reviewed.
        """
        return []  # No required columns for stub - allows any data through
    
    def get_optional_columns(self) -> List[str]:
        """
        Return optional columns for Banner Billings dataset.
        
        STUB: These are placeholder columns. Update once sample data is reviewed.
        """
        return []  # No optional columns for stub
    
    def set_sheet_name(self, sheet_name: str):
        """
        Set the current sheet name for metadata extraction.
        
        This should be called before processing each tab so that
        extraction methods can include the sheet/bill identifier.
        
        Args:
            sheet_name: Name of the current Excel sheet being processed
        """
        self.current_sheet_name = sheet_name
        self.logger.debug(f"Set current sheet name: {sheet_name}")
    
    @staticmethod
    def get_invoice_type_from_filename(filename: str) -> str:
        """
        Determine invoice type from workbook filename.
        
        Filenames contain either "Hospital" or "Professional" (e.g.
        "AZCC May 2025 Banner Hospital Invoices.xlsx"). Matching is
        case-insensitive.
        
        Args:
            filename: Workbook filename (with or without path)
            
        Returns:
            One of INVOICE_TYPE_HOSPITAL, INVOICE_TYPE_PROFESSIONAL, or INVOICE_TYPE_UNKNOWN
        """
        if not filename:
            return INVOICE_TYPE_UNKNOWN
        name = Path(filename).stem if isinstance(filename, str) else str(filename)
        name_lower = name.lower()
        if "hospital" in name_lower:
            return INVOICE_TYPE_HOSPITAL
        if "professional" in name_lower:
            return INVOICE_TYPE_PROFESSIONAL
        return INVOICE_TYPE_UNKNOWN

    @staticmethod
    def get_invoice_date_from_filename(filename: str) -> str:
        """
        Parse month/year from workbook filename and return first-of-month as YYYY-MM-01.

        Matches patterns like "September 2025", "Sep 2025", "Sept 2025".
        Returns empty string if no date found.

        Args:
            filename: Workbook filename (with or without path)

        Returns:
            Date string "YYYY-MM-01" or ""
        """
        if not filename:
            return ""
        name = Path(filename).stem if isinstance(filename, str) else str(filename)
        match = _INVOICE_DATE_PATTERN.search(name)
        if not match:
            return ""
        month_str, year_str = match.group(1).lower(), match.group(2)
        month_num = _MONTH_TO_NUM.get(month_str)
        if not month_num:
            return ""
        try:
            year = int(year_str)
        except ValueError:
            return ""
        return f"{year:04d}-{month_num:02d}-01"

    def set_workbook_name(self, workbook_name: str):
        """
        Set the current workbook name and derive invoice type from it.
        
        Args:
            workbook_name: Name of the current Excel workbook being processed
        """
        self.current_workbook_name = workbook_name
        self.current_invoice_type = self.get_invoice_type_from_filename(workbook_name)
        self.current_invoice_date = self.get_invoice_date_from_filename(workbook_name)
        self.logger.debug(
            f"Set workbook: {workbook_name}, invoice type: {self.current_invoice_type}, "
            f"invoice_date: {self.current_invoice_date or '(not found)'}"
        )
    
    @staticmethod
    def _normalize_metadata_label(val: Any) -> str:
        """
        Normalize metadata label for matching: strip, lowercase, remove trailing punctuation.
        Handles variations like "KFS NO.:", "IRB NO.:", "STUDY NAME:", etc.
        """
        if pd.isna(val):
            return ""
        s = str(val).strip().lower()
        # Strip trailing punctuation (colons, periods, etc.) so "KFS NO.:" matches "KFS NO"
        while s and not s[-1].isalnum():
            s = s[:-1]
        return s

    def _extract_metadata_label_value_pairs(
        self, df: pd.DataFrame, header_start_row: int, label_col: int, value_col: int
    ) -> Dict[str, str]:
        """
        Scan rows above the table for label/value pairs. Returns dict of
        normalized_label -> value (string). Only includes rows where label
        matches one of the expected fields for this invoice type.
        """
        if self.current_invoice_type == INVOICE_TYPE_HOSPITAL:
            expected = METADATA_FIELDS_HOSPITAL
        elif self.current_invoice_type == INVOICE_TYPE_PROFESSIONAL:
            expected = METADATA_FIELDS_PROFESSIONAL
        else:
            expected = METADATA_FIELDS_HOSPITAL + METADATA_FIELDS_PROFESSIONAL

        expected_normalized = {self._normalize_metadata_label(f): f for f in expected}
        result: Dict[str, str] = {}

        for row_idx in range(0, header_start_row):
            if label_col >= df.shape[1] or value_col >= df.shape[1]:
                break
            label_val = df.iloc[row_idx, label_col]
            value_val = df.iloc[row_idx, value_col]
            label_norm = self._normalize_metadata_label(label_val)
            if label_norm not in expected_normalized:
                continue
            canonical_key = expected_normalized[label_norm]
            if pd.isna(value_val) or str(value_val).strip() == "":
                result[canonical_key] = ""
            else:
                result[canonical_key] = str(value_val).strip()

        return result

    def extract_metadata_from_sheet(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract metadata from areas outside the main table.

        Hospital: labels in column B, values in column C.
        Professional: labels in column A, values in column B.
        Scans rows above the table header. Missing fields are left blank.

        Args:
            df: Raw DataFrame from the Excel sheet (header=None)

        Returns:
            Dictionary including sheet_name, workbook_name, invoice_type,
            extraction_timestamp, plus PI, STUDY NAME, IRB NO, KFS NO (and
            STUDY CODE for Professional).
        """
        metadata: Dict[str, Any] = {
            "sheet_name": self.current_sheet_name,
            "workbook_name": self.current_workbook_name,
            "invoice_type": self.current_invoice_type,
            "invoice_date": self.current_invoice_date,
            "extraction_timestamp": datetime.now().isoformat(),
        }

        header_start, _, _ = self._find_header_and_column_map(df)
        if header_start is None or header_start <= 0:
            self.logger.debug(
                f"No header row found for metadata scan in sheet '{self.current_sheet_name}'"
            )
            # Set all expected fields to blank
            fields = (
                METADATA_FIELDS_PROFESSIONAL
                if self.current_invoice_type == INVOICE_TYPE_PROFESSIONAL
                else METADATA_FIELDS_HOSPITAL
            )
            for f in fields:
                metadata[f] = ""
            return metadata

        if self.current_invoice_type == INVOICE_TYPE_HOSPITAL:
            label_col, value_col = 1, 2  # B, C
            fields = METADATA_FIELDS_HOSPITAL
        elif self.current_invoice_type == INVOICE_TYPE_PROFESSIONAL:
            label_col, value_col = 0, 1  # A, B
            fields = METADATA_FIELDS_PROFESSIONAL
        else:
            label_col, value_col = 1, 2
            fields = METADATA_FIELDS_HOSPITAL

        pairs = self._extract_metadata_label_value_pairs(
            df, header_start, label_col, value_col
        )
        for f in fields:
            metadata[f] = pairs.get(f, "")

        self.logger.debug(
            f"Extracted metadata from sheet '{self.current_sheet_name}': "
            f"{list(metadata.keys())}"
        )
        return metadata
    
    @staticmethod
    def _normalize_header(val: Any) -> str:
        """Normalize header value for matching: strip, lowercase."""
        if pd.isna(val):
            return ""
        return str(val).strip().lower()

    @staticmethod
    def _parse_currency(val: Any) -> Optional[float]:
        """Parse currency value ($1,234.56) to float."""
        if pd.isna(val):
            return None
        s = str(val).strip().replace("$", "").replace(",", "")
        if not s:
            return None
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    def _find_header_and_column_map(
        self, df: pd.DataFrame
    ) -> Tuple[Optional[int], Optional[int], Dict[str, int]]:
        """
        Find header row(s) and build column index map for target columns.

        Hospital: 1 header row. Professional: 2 header rows (some merged cells).
        Searches from row 10 downward. Returns (header_start_row, data_start_row,
        {col_name: col_index}) or (None, None, {}) if not found.
        """
        target_lower = [c.lower() for c in TARGET_COLUMNS]
        header_rows = (
            PROFESSIONAL_HEADER_ROWS
            if self.current_invoice_type == INVOICE_TYPE_PROFESSIONAL
            else HOSPITAL_HEADER_ROWS
        )
        # Unknown: try 1-row first, then 2-row
        try_order = (
            [1, 2]
            if self.current_invoice_type == INVOICE_TYPE_UNKNOWN
            else [header_rows]
        )

        for n_rows in try_order:
            for start_row in range(10, min(40, len(df) - n_rows + 1)):
                col_map: Dict[str, int] = {}
                for col_idx in range(df.shape[1]):
                    for r in range(n_rows):
                        row_idx = start_row + r
                        if row_idx >= len(df):
                            break
                        val = df.iloc[row_idx, col_idx]
                        normalized = self._normalize_header(val)
                        for target, target_low in zip(TARGET_COLUMNS, target_lower):
                            if normalized == target_low and target not in col_map:
                                col_map[target] = col_idx
                                break
                if len(col_map) == 3:
                    data_start = start_row + n_rows
                    return (start_row, data_start, col_map)

        return (None, None, {})

    def _find_data_end_row(self, df: pd.DataFrame, data_start_row: int) -> int:
        """
        Find the first row index that ends the data table.
        Stops at first completely empty row, or row containing TABLE_END_MARKERS.
        """
        for row_idx in range(data_start_row, len(df)):
            row = df.iloc[row_idx]
            # Check for end markers
            for val in row:
                if pd.notna(val) and isinstance(val, str):
                    v = val.strip().upper()
                    for marker in TABLE_END_MARKERS:
                        if marker in v:
                            return row_idx
            # First completely empty row
            is_empty = True
            for v in row:
                if pd.notna(v) and str(v).strip():
                    is_empty = False
                    break
            if is_empty:
                return row_idx
        return len(df)

    def find_table_bounds(self, df: pd.DataFrame) -> Tuple[int, int, int, int]:
        """
        Detect the bounds of the main data table within the sheet.

        Uses header detection and table-end rules. Returns
        (data_start_row, data_end_row, start_col, end_col).
        """
        header_start, data_start, col_map = self._find_header_and_column_map(df)
        if header_start is None or data_start is None or not col_map:
            self.logger.warning(
                f"Could not find header/target columns in sheet '{self.current_sheet_name}'"
            )
            return (0, 0, 0, 0)

        data_end = self._find_data_end_row(df, data_start)
        col_indices = list(col_map.values())
        start_col = min(col_indices)
        end_col = max(col_indices) + 1

        return (data_start, data_end, start_col, end_col)

    def extract_table_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract the main data table from the sheet.

        Extracts only Charge Amount, Adjustment, Balance Due. Header detection
        and table bounds differ by invoice type (Hospital: 1 header row;
        Professional: 2 header rows). Parses currency values and skips rows
        with empty target columns.

        Args:
            df: Raw DataFrame from the Excel sheet (header=None)

        Returns:
            DataFrame with columns: Charge Amount, Adjustment, Balance Due
        """
        header_start, data_start, col_map = self._find_header_and_column_map(df)
        if header_start is None or data_start is None or len(col_map) != 3:
            self.logger.warning(
                f"Could not find target columns in sheet '{self.current_sheet_name}', "
                f"invoice_type={self.current_invoice_type}"
            )
            return pd.DataFrame(columns=TARGET_COLUMNS)

        data_end = self._find_data_end_row(df, data_start)

        rows = []
        for row_idx in range(data_start, data_end):
            row = df.iloc[row_idx]
            values = {}
            all_present = True
            for col_name in TARGET_COLUMNS:
                col_idx = col_map[col_name]
                raw = row.iloc[col_idx] if col_idx < len(row) else None
                parsed = self._parse_currency(raw)
                values[col_name] = parsed
                if parsed is None:
                    all_present = False

            # Skip rows where any target column is empty
            if all_present:
                rows.append(values)

        return pd.DataFrame(rows, columns=TARGET_COLUMNS)
    
    def extract_sheet_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract all data from a single sheet (metadata + table).
        
        Args:
            df: Raw DataFrame from the Excel sheet
            
        Returns:
            Dictionary containing:
            - 'metadata': Dict of extracted metadata
            - 'table_data': List of row dictionaries from the table
            - 'raw_row_count': Number of rows in raw data
        """
        # Extract metadata from outside the table
        metadata = self.extract_metadata_from_sheet(df)
        
        # Extract the table data
        table_df = self.extract_table_data(df)
        
        # All metadata keys that may appear on rows (unified so combined sheet has consistent columns)
        all_meta_keys = list(
            dict.fromkeys(METADATA_FIELDS_HOSPITAL + METADATA_FIELDS_PROFESSIONAL)
        )
        
        # Convert table to list of dicts
        table_rows = []
        for _, row in table_df.iterrows():
            row_dict = {}
            for col in table_df.columns:
                value = row[col]
                # Convert NaN to None
                if pd.isna(value):
                    row_dict[str(col)] = None
                else:
                    row_dict[str(col)] = value
            
            # Only include rows that have some data
            if any(v is not None and str(v).strip() != '' for v in row_dict.values()):
                # Add extracted metadata to each row (blank if not in this invoice type)
                for key in all_meta_keys:
                    row_dict[key] = metadata.get(key, "")
                # Add invoice date (from workbook filename)
                row_dict["invoice_date"] = self.current_invoice_date
                # Add source tracking
                row_dict["_sheet_name"] = self.current_sheet_name
                row_dict['_workbook_name'] = self.current_workbook_name
                row_dict['_invoice_type'] = self.current_invoice_type
                table_rows.append(row_dict)
        
        return {
            'metadata': metadata,
            'table_data': table_rows,
            'raw_row_count': len(df)
        }
    
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
                # Read with header=None to get raw data including any header rows
                df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                if not df.empty:
                    tabs.append((sheet_name, df))
                    logger.info(f"Parsed tab '{sheet_name}': {len(df)} rows, {len(df.columns)} columns")
            return tabs
        except Exception as e:
            logger.error(f"Error parsing Excel tabs: {e}")
            raise
    
    def process_workbook(self, file_path: str, workbook_name: str = None) -> List[Dict[str, Any]]:
        """
        Process an entire workbook and extract data from all tabs.
        
        Args:
            file_path: Path to the Excel file
            workbook_name: Optional name for the workbook (defaults to filename)
            
        Returns:
            List of extracted data dictionaries, one per tab
        """
        if workbook_name:
            self.set_workbook_name(workbook_name)
        else:
            self.set_workbook_name(Path(file_path).name)
        
        tabs = self.parse_excel_tabs(file_path)
        
        all_sheet_data = []
        for sheet_name, df in tabs:
            self.set_sheet_name(sheet_name)
            sheet_data = self.extract_sheet_data(df)
            all_sheet_data.append(sheet_data)
            logger.info(
                f"Processed sheet '{sheet_name}': "
                f"{len(sheet_data['table_data'])} data rows extracted"
            )
        
        return all_sheet_data
    
    def transform_rows(self, valid_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform validated rows before output.
        
        STUB: Maps column names and applies transformations.
        Update once column mapping is defined.
        
        Args:
            valid_rows: List of validated row dictionaries
            
        Returns:
            List of transformed row dictionaries
        """
        transformed_rows = []
        
        for row in valid_rows:
            transformed_row = {}
            
            for col_name, value in row.items():
                # Map column name to snake_case
                db_col_name = self._map_column_names(col_name)
                
                # Handle None/empty values
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    transformed_row[db_col_name] = None
                else:
                    transformed_row[db_col_name] = value
            
            transformed_rows.append(transformed_row)
        
        self.logger.debug(f"Transformed {len(transformed_rows)} rows")
        return transformed_rows
    
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
        Write transformed data to database.
        
        NOTE: Database write is NOT implemented for Banner Billings.
        This processor is designed for file-to-file transformation only.
        
        Args:
            valid_rows: List of transformed row dictionaries
            db_session: Database session (not used)
            upload_timestamp: ISO format timestamp of the upload
            source_filename: Name of the uploaded file
            upload_batch_id: Optional batch ID
            source_tab_name: Name of the Excel tab
            
        Returns:
            0 (no rows written - DB not implemented)
        """
        self.logger.warning(
            "write_to_database called on BannerBillingsProcessor but DB write "
            "is not implemented. This processor is for file-to-file transformation only."
        )
        return 0
