"""
Clinical Trials API endpoints for Banner Billings processing.

This router handles file uploads for clinical trials billing data,
processes the files, and returns a downloadable Excel report.
"""
import logging
import uuid
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import StreamingResponse
from backend.core.config import settings
from backend.services.processors.banner_billings_processor import BannerBillingsProcessor
from backend.services.transformations.banner_combiner import BannerBillingsCombiner
from backend.services.transformations.banner_summarizer import BannerBillingsSummarizer
from backend.services.reports.excel_generator import ExcelReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/process-billings",
    summary="Process Banner Billing files and generate report",
    description=(
        "Upload one or more Excel files containing Banner billing data. "
        "Each file can contain multiple tabs (one bill per tab). "
        "Returns a downloadable Excel report with combined data and summary."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Excel report file",
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}
            }
        },
        400: {"description": "Invalid file type or processing error"},
        500: {"description": "Internal server error"}
    }
)
async def process_banner_billings(
    files: List[UploadFile] = File(
        ...,
        description="Excel files (.xlsx, .xls) containing Banner billing data"
    )
):
    """
    Process Banner Billing Excel files and generate a combined report.
    
    This endpoint:
    1. Accepts one or more Excel file uploads
    2. Extracts data from all tabs in each file
    3. Combines all extracted data into a single dataset
    4. Generates a formatted Excel report with summary and data sheets
    5. Returns the report as a downloadable file
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
        if file_extension not in ["xlsx", "xls"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension} in {file.filename}. "
                       f"Only Excel files (.xlsx, .xls) are supported."
            )
    
    # Create temp directory if needed
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files: List[Path] = []
    
    try:
        logger.info(f"Processing {len(files)} Banner Billing file(s)")
        
        # Save uploaded files to temp storage
        for file in files:
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            saved_path = temp_dir / f"{file_id}{file_extension}"
            
            content = await file.read()
            with open(saved_path, "wb") as f:
                f.write(content)
            
            saved_files.append(saved_path)
            logger.debug(f"Saved uploaded file: {file.filename} -> {saved_path}")
        
        # Initialize processor and combiner
        processor = BannerBillingsProcessor()
        combiner = BannerBillingsCombiner()
        
        # Process each workbook
        for saved_path, original_file in zip(saved_files, files):
            try:
                workbook_data = processor.process_workbook(
                    str(saved_path),
                    workbook_name=original_file.filename
                )
                combiner.add_workbook_data(workbook_data)
                logger.info(
                    f"Processed workbook '{original_file.filename}': "
                    f"{len(workbook_data)} sheets"
                )
            except Exception as e:
                logger.error(
                    f"Error processing workbook '{original_file.filename}': {e}",
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error processing file '{original_file.filename}': {str(e)}"
                )
        
        # Validate combined data
        validation_issues = combiner.validate_combined_data()
        if validation_issues:
            logger.warning(f"Validation issues: {validation_issues}")
            # Continue anyway - these are warnings, not errors
        
        # Get combined data and summary
        combined_df = combiner.get_combined_dataframe()
        summary_data = combiner.get_summary_data()

        # Generate aggregated summaries
        study_summary_df, account_summary_df = BannerBillingsSummarizer.get_summaries(
            combined_df
        )

        # Generate Excel report
        generator = ExcelReportGenerator()
        output_buffer = generator.generate_report(
            combined_df,
            summary_data,
            study_summary_df=study_summary_df,
            account_summary_df=account_summary_df,
        )
        
        # Generate filename
        output_filename = generator.generate_filename("banner_billings")
        
        logger.info(
            f"Generated report '{output_filename}': "
            f"{len(combined_df)} rows from {len(files)} file(s)"
        )
        
        # Return as streaming response for download
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{output_filename}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Banner Billing files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing files: {str(e)}"
        )
    finally:
        # Clean up temporary files
        for saved_path in saved_files:
            if saved_path.exists():
                saved_path.unlink()
                logger.debug(f"Cleaned up temporary file: {saved_path}")


@router.get(
    "/status",
    summary="Get Clinical Trials module status",
    description="Check if the Clinical Trials processing module is operational."
)
async def get_clinical_trials_status():
    """
    Get status of the Clinical Trials module.
    
    Returns basic status information for health checks.
    """
    return {
        "module": "clinical_trials",
        "status": "operational",
        "processor": "banner_billings",
        "supported_file_types": ["xlsx", "xls"],
        "timestamp": datetime.now().isoformat()
    }
