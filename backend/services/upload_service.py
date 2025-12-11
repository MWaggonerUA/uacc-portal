"""
Service for handling file uploads, parsing, and validation.

This service handles:
- Saving uploaded files to temporary storage
- Parsing CSV and Excel files (including multi-tab Excel for iLabs)
- Auto-detecting dataset types from column headers
- Processing multiple files in parallel
- Writing validated data to database using dataset-specific processors
"""
import os
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.models.upload_models import UploadSummary, UploadError, UploadResponse
from backend.services.processors.processor_factory import get_processor_for_dataframe
from backend.services.processors.ilabs_processor import ILabsProcessor

logger = logging.getLogger(__name__)


class UploadService:
    """Service for processing file uploads with dataset-specific processors."""
    
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> Path:
        """
        Save uploaded file to temporary storage.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Path to saved file
        """
        # Generate unique filename to avoid conflicts
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ".tmp"
        saved_path = self.temp_dir / f"{file_id}{file_extension}"
        
        # Write file to disk
        with open(saved_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.debug(f"Saved uploaded file: {saved_path}")
        return saved_path
    
    def parse_file(self, file_path: Path) -> Tuple[List[pd.DataFrame], str, Optional[str]]:
        """
        Parse CSV or Excel file into pandas DataFrame(s).
        
        For iLabs Excel files with multiple tabs, returns multiple DataFrames.
        For other files, returns a single DataFrame in a list.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (list_of_dataframes, file_type, dataset_type_hint)
            dataset_type_hint is 'ilabs' if Excel with multiple tabs, None otherwise
        """
        file_extension = file_path.suffix.lower()
        dataframes = []
        dataset_hint = None
        
        if file_extension == ".csv":
            df = pd.read_csv(file_path)
            dataframes.append(df)
            file_type = "csv"
        elif file_extension in [".xlsx", ".xls"]:
            # Check if this might be an iLabs file (multiple tabs)
            excel_file = pd.ExcelFile(file_path)
            if len(excel_file.sheet_names) > 1:
                # Multiple tabs - likely iLabs
                dataset_hint = "ilabs"
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    if not df.empty:
                        dataframes.append(df)
                logger.info(f"Parsed iLabs Excel file with {len(dataframes)} tabs")
            else:
                # Single tab - regular Excel file
                df = pd.read_excel(file_path)
                dataframes.append(df)
            file_type = "xlsx"
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return dataframes, file_type, dataset_hint
    
    async def process_single_file(
        self,
        file: UploadFile,
        db_session: Optional[AsyncSession] = None,
        preview_rows: int = 5
    ) -> UploadSummary:
        """
        Process a single uploaded file: save, parse, validate, and optionally write to DB.
        
        Args:
            file: FastAPI UploadFile object
            db_session: Optional database session for writing to DB
            preview_rows: Number of rows to include in preview
            
        Returns:
            UploadSummary with processing results
        """
        upload_timestamp = datetime.now().isoformat()
        saved_path = None
        
        try:
            # Save file
            saved_path = await self.save_uploaded_file(file)
            logger.info(f"Processing file: {file.filename}")
            
            # Parse file (may return multiple DataFrames for iLabs)
            dataframes, file_type, dataset_hint = self.parse_file(saved_path)
            
            # Process each DataFrame (usually just one, but multiple for iLabs)
            all_valid_rows = []
            all_errors = []
            total_rows = 0
            dataset_type = None
            row_number_offset = 0  # Track cumulative row count for unique row numbering across tabs
            
            # If we have a dataset hint (e.g., 'ilabs' for multi-tab Excel), use it directly
            processor = None
            if dataset_hint:
                from backend.services.processors.processor_factory import get_processor
                processor = get_processor(dataset_hint)
                if processor:
                    logger.info(f"Using dataset hint '{dataset_hint}' to select processor")
                    dataset_type = dataset_hint
            
            for df_idx, df in enumerate(dataframes):
                # Use hint-based processor if available, otherwise auto-detect
                if not processor:
                    processor = get_processor_for_dataframe(df)
                
                if not processor:
                    error_msg = "Could not auto-detect dataset type from column headers"
                    logger.error(f"{error_msg}. Columns: {list(df.columns)}")
                    # Add error for all rows with offset row numbers
                    for idx in range(len(df)):
                        all_errors.append(UploadError(
                            row_number=row_number_offset + idx + 2,  # Offset by previous rows
                            column=None,
                            message=error_msg,
                            value=None
                        ))
                    total_rows += len(df)
                    row_number_offset += len(df)  # Update offset for next tab
                    continue
                
                if not dataset_type:
                    dataset_type = processor.dataset_type
                
                dataset_type = processor.dataset_type
                logger.info(f"Detected dataset type: {dataset_type} for DataFrame {df_idx + 1}")
                
                # Validate using processor
                valid_rows, errors = processor.validate_dataframe(df)
                
                # Adjust row numbers in errors to be unique across tabs
                # Create new error objects with offset row numbers
                adjusted_errors = []
                for error in errors:
                    if error.row_number > 0:
                        # Create new error with offset row number
                        adjusted_errors.append(UploadError(
                            row_number=row_number_offset + error.row_number,
                            column=error.column,
                            message=error.message,
                            value=error.value
                        ))
                    else:
                        adjusted_errors.append(error)
                errors = adjusted_errors
                
                # Write to database if session provided
                if db_session and valid_rows:
                    try:
                        inserted_count = await processor.write_to_database(
                            valid_rows=valid_rows,
                            db_session=db_session,
                            upload_timestamp=upload_timestamp
                        )
                        logger.info(f"Inserted {inserted_count} rows into database for {dataset_type}")
                    except Exception as e:
                        logger.error(f"Error writing to database: {e}", exc_info=True)
                        # Add database error to errors list with proper offset
                        for row_num in range(len(valid_rows)):
                            all_errors.append(UploadError(
                                row_number=row_number_offset + row_num + 2,
                                column=None,
                                message=f"Database write error: {str(e)}",
                                value=None
                            ))
                
                all_valid_rows.extend(valid_rows)
                all_errors.extend(errors)
                total_rows += len(df)
                row_number_offset += len(df)  # Update offset for next tab
            
            # Calculate unique rows with errors (not total error count)
            rows_with_errors = set(error.row_number for error in all_errors if error.row_number > 0)
            invalid_rows_count = len(rows_with_errors)
            
            # Create preview (first N valid rows)
            preview_data = all_valid_rows[:preview_rows] if all_valid_rows else None
            
            # Build summary
            summary = UploadSummary(
                total_rows=total_rows,
                valid_rows=len(all_valid_rows),
                invalid_rows=invalid_rows_count,
                errors=all_errors[:100],  # Limit errors in response (first 100)
                file_name=file.filename or "unknown",
                file_type=file_type,
                preview_data=preview_data
            )
            
            logger.info(
                f"Processed {file.filename}: {summary.valid_rows} valid, "
                f"{summary.invalid_rows} errors out of {summary.total_rows} total rows"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
            # Return error summary
            return UploadSummary(
                total_rows=0,
                valid_rows=0,
                invalid_rows=1,
                errors=[UploadError(
                    row_number=0,
                    column=None,
                    message=f"File processing error: {str(e)}",
                    value=None
                )],
                file_name=file.filename or "unknown",
                file_type="unknown",
                preview_data=None
            )
        finally:
            # Clean up: delete temporary file
            if saved_path and saved_path.exists():
                saved_path.unlink()
                logger.debug(f"Cleaned up temporary file: {saved_path}")
    
    async def process_multiple_files(
        self,
        files: List[UploadFile],
        db_session: Optional[AsyncSession] = None,
        parallel: bool = True,
        preview_rows: int = 5
    ) -> List[UploadSummary]:
        """
        Process multiple uploaded files.
        
        Args:
            files: List of FastAPI UploadFile objects
            db_session: Optional database session for writing to DB
            parallel: If True, process files in parallel (faster but more resource-intensive)
            preview_rows: Number of rows to include in preview
            
        Returns:
            List of UploadSummary objects (one per file)
        """
        logger.info(f"Processing {len(files)} file(s) (parallel={parallel})")
        
        if parallel and len(files) > 1:
            # Process files in parallel
            tasks = [
                self.process_single_file(file, db_session, preview_rows)
                for file in files
            ]
            summaries = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            results = []
            for i, summary in enumerate(summaries):
                if isinstance(summary, Exception):
                    logger.error(f"Error processing file {files[i].filename}: {summary}", exc_info=True)
                    results.append(UploadSummary(
                        total_rows=0,
                        valid_rows=0,
                        invalid_rows=1,
                        errors=[UploadError(
                            row_number=0,
                            column=None,
                            message=f"Processing error: {str(summary)}",
                            value=None
                        )],
                        file_name=files[i].filename or "unknown",
                        file_type="unknown",
                        preview_data=None
                    ))
                else:
                    results.append(summary)
            
            return results
        else:
            # Process files sequentially
            results = []
            for file in files:
                summary = await self.process_single_file(file, db_session, preview_rows)
                results.append(summary)
            return results
    
    # Legacy method for backward compatibility
    async def process_upload(
        self,
        file: UploadFile,
        preview_rows: int = 5
    ) -> UploadSummary:
        """
        Legacy method: Process a single file without database write.
        
        Use process_single_file() for new code.
        """
        return await self.process_single_file(file, db_session=None, preview_rows=preview_rows)


# Singleton instance
upload_service = UploadService()
