"""
Combiner for Banner Billings data.

This module combines extracted data from multiple sheets and workbooks
into a single unified dataset ready for report generation.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class BannerBillingsCombiner:
    """
    Combines Banner Billings data from multiple sheets/workbooks.
    
    Takes extracted data from the BannerBillingsProcessor and:
    1. Aggregates all table rows into a single DataFrame
    2. Collects metadata for summary generation
    3. Validates combined data for consistency
    """
    
    def __init__(self):
        """Initialize the combiner."""
        self.combined_rows: List[Dict[str, Any]] = []
        self.metadata_records: List[Dict[str, Any]] = []
        self.source_files: List[str] = []
        self.processing_timestamp: str = datetime.now().isoformat()
    
    def reset(self):
        """Reset the combiner state for a new processing run."""
        self.combined_rows = []
        self.metadata_records = []
        self.source_files = []
        self.processing_timestamp = datetime.now().isoformat()
    
    def add_sheet_data(self, sheet_data: Dict[str, Any]):
        """
        Add extracted data from a single sheet.
        
        Args:
            sheet_data: Dictionary containing:
                - 'metadata': Dict of extracted metadata
                - 'table_data': List of row dictionaries from the table
                - 'raw_row_count': Number of rows in raw data
        """
        # Store metadata
        metadata = sheet_data.get('metadata', {})
        metadata['raw_row_count'] = sheet_data.get('raw_row_count', 0)
        metadata['extracted_row_count'] = len(sheet_data.get('table_data', []))
        self.metadata_records.append(metadata)
        
        # Track source file
        workbook_name = metadata.get('workbook_name')
        if workbook_name and workbook_name not in self.source_files:
            self.source_files.append(workbook_name)
        
        # Add table rows
        table_data = sheet_data.get('table_data', [])
        self.combined_rows.extend(table_data)
        
        logger.debug(
            f"Added sheet data: {metadata.get('sheet_name', 'unknown')} "
            f"({len(table_data)} rows)"
        )
    
    def add_workbook_data(self, workbook_data: List[Dict[str, Any]]):
        """
        Add extracted data from an entire workbook (multiple sheets).
        
        Args:
            workbook_data: List of sheet_data dictionaries from BannerBillingsProcessor
        """
        for sheet_data in workbook_data:
            self.add_sheet_data(sheet_data)
    
    def get_combined_dataframe(self) -> pd.DataFrame:
        """
        Get all combined data as a pandas DataFrame.
        
        Returns:
            DataFrame with all combined rows
        """
        if not self.combined_rows:
            logger.warning("No data to combine - returning empty DataFrame")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.combined_rows)
        
        # Clean up internal tracking columns if desired
        # (keeping them for now as they're useful for traceability)
        
        logger.info(f"Combined DataFrame: {len(df)} rows, {len(df.columns)} columns")
        return df
    
    def get_summary_data(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the combined data.
        
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'processing_timestamp': self.processing_timestamp,
            'total_source_files': len(self.source_files),
            'source_files': self.source_files,
            'total_sheets_processed': len(self.metadata_records),
            'total_rows_extracted': len(self.combined_rows),
            'sheets': []
        }
        
        # Metadata field names (for summary/report)
        meta_field_names = [
            'PI', 'STUDY NAME', 'STUDY CODE', 'IRB NO', 'KFS NO'
        ]
        # Add per-sheet summary (include extracted metadata)
        for metadata in self.metadata_records:
            sheet_summary = {
                'workbook': metadata.get('workbook_name', 'unknown'),
                'sheet': metadata.get('sheet_name', 'unknown'),
                'invoice_type': metadata.get('invoice_type', 'unknown'),
                'invoice_date': metadata.get('invoice_date', ''),
                'raw_rows': metadata.get('raw_row_count', 0),
                'extracted_rows': metadata.get('extracted_row_count', 0),
            }
            for key in meta_field_names:
                sheet_summary[key] = metadata.get(key, '')
            summary['sheets'].append(sheet_summary)
        
        return summary
    
    def validate_combined_data(self) -> List[str]:
        """
        Validate the combined data for consistency issues.
        
        Returns:
            List of warning/error messages (empty if valid)
        """
        issues = []
        
        if not self.combined_rows:
            issues.append("No data extracted from any sheets")
            return issues
        
        # Check for column consistency across rows
        all_columns = set()
        for row in self.combined_rows:
            all_columns.update(row.keys())
        
        # Check for rows with missing columns
        rows_with_missing = 0
        for row in self.combined_rows:
            if len(row.keys()) < len(all_columns):
                rows_with_missing += 1
        
        if rows_with_missing > 0:
            issues.append(
                f"{rows_with_missing} rows have fewer columns than others "
                f"(total columns found: {len(all_columns)})"
            )
        
        # Check for completely empty rows
        empty_rows = sum(
            1 for row in self.combined_rows 
            if all(v is None or str(v).strip() == '' for v in row.values())
        )
        if empty_rows > 0:
            issues.append(f"{empty_rows} empty rows found in combined data")
        
        return issues
    
    def get_column_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics for each column in the combined data.
        
        Returns:
            Dictionary mapping column names to their statistics
        """
        if not self.combined_rows:
            return {}
        
        df = self.get_combined_dataframe()
        
        column_stats = {}
        for col in df.columns:
            non_null = df[col].notna().sum()
            column_stats[col] = {
                'non_null_count': int(non_null),
                'null_count': int(len(df) - non_null),
                'fill_rate': round(non_null / len(df) * 100, 1) if len(df) > 0 else 0,
                'sample_values': df[col].dropna().head(3).tolist()
            }
        
        return column_stats
