"""
Pydantic models for file upload operations.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UploadError(BaseModel):
    """Represents a validation or processing error for a specific row."""
    row_number: int = Field(..., description="Row number in the file (1-indexed)")
    column: Optional[str] = Field(None, description="Column name where error occurred")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="The value that caused the error")


class UploadSummary(BaseModel):
    """Summary of file upload processing results."""
    total_rows: int = Field(..., description="Total number of rows processed")
    valid_rows: int = Field(..., description="Number of rows that passed validation")
    invalid_rows: int = Field(..., description="Number of rows with validation errors")
    errors: List[UploadError] = Field(default_factory=list, description="List of validation errors")
    file_name: str = Field(..., description="Name of the uploaded file")
    file_type: str = Field(..., description="File type (csv, xlsx, etc.)")
    processed_at: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    preview_data: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Preview of first few valid rows (for display purposes)"
    )


class UploadResponse(BaseModel):
    """Response model for single file upload endpoints."""
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Human-readable message")
    summary: Optional[UploadSummary] = Field(None, description="Processing summary if available")
    file_id: Optional[str] = Field(None, description="Unique identifier for the uploaded file (for future tracking)")


class MultiUploadResponse(BaseModel):
    """Response model for multiple file upload endpoints."""
    total_files: int = Field(..., description="Total number of files processed")
    successful_files: int = Field(..., description="Number of files processed successfully")
    failed_files: int = Field(..., description="Number of files that failed")
    summaries: List[UploadSummary] = Field(..., description="Processing summary for each file")
    overall_success: bool = Field(..., description="True if all files processed successfully")
    message: str = Field(..., description="Human-readable summary message")

