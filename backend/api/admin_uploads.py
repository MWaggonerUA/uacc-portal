"""
Admin upload endpoints for raw data file processing.

This router handles file uploads for administrators and processes them
through the upload service pipeline with auto-detection of dataset types.
"""
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.models.upload_models import UploadResponse, UploadSummary, MultiUploadResponse
from backend.services.upload_service import upload_service
from backend.services.db import get_db
from backend.core.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/uploads/raw-data",
    response_model=UploadResponse,
    summary="Upload and process a single raw data file",
    description="Upload a single CSV or Excel file for processing and validation. "
                "Dataset type is auto-detected from column headers. "
                "For multiple files, use /uploads/raw-data-multiple endpoint."
)
async def upload_raw_data(
    file: UploadFile = File(..., description="CSV or Excel file to upload"),
    write_to_db: bool = Query(False, description="Whether to write validated data to database"),
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_admin),  # Uncomment when RBAC is implemented
) -> UploadResponse:
    """
    Upload and process a raw data file.
    
    This endpoint:
    1. Accepts file upload (CSV or Excel)
    2. Saves file to temporary storage
    3. Parses and validates the data
    4. Returns processing summary with preview
    
    Future enhancements:
    - Write validated data to database
    - Support different file types (RLOGX, publications, etc.)
    - Async processing for large files
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    file_extension = file.filename.lower().split(".")[-1]
    if file_extension not in ["csv", "xlsx", "xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Supported types: csv, xlsx, xls"
        )
    
    try:
        # Process upload (with optional DB write)
        db_session = db if write_to_db else None
        summary: UploadSummary = await upload_service.process_single_file(
            file, 
            db_session=db_session
        )
        
        # Build response
        success = summary.invalid_rows == 0
        
        message = (
            f"Processed {summary.total_rows} rows. "
            f"{summary.valid_rows} valid, {summary.invalid_rows} with errors."
        )
        if write_to_db and summary.valid_rows > 0:
            message += f" {summary.valid_rows} rows written to database."
        
        return UploadResponse(
            success=success,
            message=message,
            summary=summary,
            file_id=None  # TODO: Generate and track file IDs
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.post(
    "/uploads/raw-data-multiple",
    response_model=MultiUploadResponse,
    summary="Upload and process multiple raw data files",
    description="Upload multiple CSV or Excel files for processing and validation. "
                "Dataset types are auto-detected from column headers. "
                "Files are processed in parallel for better performance. "
                "All files are processed even if some fail."
)
async def upload_multiple_raw_data(
    files: List[UploadFile] = File(..., description="CSV or Excel files to upload"),
    write_to_db: bool = Query(False, description="Whether to write validated data to database"),
    parallel: bool = Query(True, description="Process files in parallel (faster)"),
    db: AsyncSession = Depends(get_db),
    # current_user: dict = Depends(require_admin),  # Uncomment when RBAC is implemented
) -> MultiUploadResponse:
    """
    Upload and process multiple raw data files.
    
    This endpoint:
    1. Accepts multiple file uploads (CSV or Excel)
    2. Auto-detects dataset type for each file from column headers
    3. Processes files in parallel (if enabled)
    4. Validates data using dataset-specific processors
    5. Optionally writes validated data to database
    6. Returns summary for each file
    
    Features:
    - Continues processing even if some files fail
    - Handles iLabs Excel files with multiple tabs
    - Supports multiple files of the same dataset type (e.g., publications)
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required"
        )
    
    # Validate file types
    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All files must have filenames"
            )
        
        file_extension = file.filename.lower().split(".")[-1]
        if file_extension not in ["csv", "xlsx", "xls"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension} in {file.filename}. Supported types: csv, xlsx, xls"
            )
    
    try:
        logger.info(f"Processing {len(files)} file(s) (parallel={parallel}, write_to_db={write_to_db})")
        
        # Process all files
        db_session = db if write_to_db else None
        summaries = await upload_service.process_multiple_files(
            files=files,
            db_session=db_session,
            parallel=parallel
        )
        
        # Calculate overall statistics
        successful = sum(1 for s in summaries if s.invalid_rows == 0)
        failed = len(summaries) - successful
        overall_success = failed == 0
        
        total_rows = sum(s.total_rows for s in summaries)
        total_valid = sum(s.valid_rows for s in summaries)
        total_errors = sum(s.invalid_rows for s in summaries)
        
        message = (
            f"Processed {len(files)} file(s): {successful} successful, {failed} failed. "
            f"Total: {total_rows} rows ({total_valid} valid, {total_errors} errors)."
        )
        if write_to_db and total_valid > 0:
            message += f" {total_valid} rows written to database."
        
        return MultiUploadResponse(
            total_files=len(files),
            successful_files=successful,
            failed_files=failed,
            summaries=summaries,
            overall_success=overall_success,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error processing multiple files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing files: {str(e)}"
        )


@router.get(
    "/uploads/status",
    summary="Get upload status",
    description="Placeholder endpoint for checking upload processing status."
)
async def get_upload_status(
    # current_user: dict = Depends(require_admin),  # Uncomment when RBAC is implemented
):
    """
    Get status of recent uploads.
    
    TODO: Implement tracking of upload history.
    """
    return {
        "message": "Upload status endpoint - to be implemented",
        "recent_uploads": []
    }

