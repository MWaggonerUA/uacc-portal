# UACC Portal - Project Status

**Last Updated:** 2026-02-02

---

## What Problem This Project Solves

The UACC Portal is an internal modular web application that solves the problem of **managing, validating, and storing research data** for the University of Arizona Cancer Center (UACC). 

Specifically, it provides:
- **Automated data upload and validation** for multiple research dataset types (budgets, funding, membership, publications, proposals, iLabs)
- **Clinical Trials data processing** for Banner Billing Excel workbooks (multi-tab, one bill per tab)—extracts data, combines across files, and generates formatted reports
- **Schema auto-detection** from uploaded CSV/Excel files
- **Data quality assurance** through row-level validation with detailed error reporting
- **Centralized data storage** in MySQL database with proper schema and metadata tracking
- **Admin interface** for bulk file processing with parallel upload support

The system eliminates manual data entry errors, standardizes data formats, and provides a foundation for future dashboards and reporting tools.

---

## Current Phase: **STABILIZE**

The core functionality is **built and operational**, but the system needs refinement and stabilization:

✅ **Completed:**
- FastAPI backend with async database layer
- Dash frontend for admin uploads
- 6 dataset processors (budgets, funding, membership, publications, proposals, iLabs)
- **Clinical Trials module** — Banner Billings processor, transformations, report generator, upload UI at `/clinicaltrialsupload`
- Auto-detection of dataset types from column headers
- Validation pipeline with error reporting
- Database ORM models for all dataset types
- Multi-file parallel processing

⚠️ **In Progress / Needs Work:**
- Column mapping is not working correctly (generic snake_case conversion instead of explicit mappings)
- Data type conversions are incomplete (only dates are handled)
- Unwanted columns are being written to database
- Need explicit column mapping configuration

---

## Last Thing I Touched

**Date:** 2026-01-21

**Activity:** Reviewed project status and identified column mapping issues

**Details:**
- Uploaded sample files for each dataset type
- Reviewed what's being written to database
- Discovered that column mapping is not working as expected:
  - Generic `_map_column_names()` converts all columns to snake_case automatically
  - No explicit mapping from source column names to target database columns
  - Unwanted columns are being included in database writes
  - Data type conversions are only happening for dates, not other types (int, float, bool, etc.)

**Next Action Identified:**
- Need to implement explicit column mapping configuration
- Need to add column removal/filtering logic
- Need to add comprehensive data type conversion

---

## Clinical Trials Module (Added 2026-02-02)

**Activity:** Scaffolded new `clinical_trials` module for Banner Billing data processing; refined extraction logic using sample workbooks in `data/`.

**What Was Built:**
- **Processor** (`backend/services/processors/banner_billings_processor.py`) — Extracts data from multi-tab Excel workbooks (one bill per tab).
  - **Invoice type from filename:** Workbook filename must contain "Hospital" or "Professional" (case-insensitive); type is stored in metadata and on each row and drives header/layout handling.
  - **Hospital invoices:** Single header row; table in column A. Target columns: Charge Amount, Adjustment, Balance Due.
  - **Professional invoices:** Two-row header (rows 23–24); some columns merged. Same target columns.
  - **Table detection:** Header found by searching for the three target column names (case-insensitive, trim spaces). Table ends at first completely empty row or at text "TOTAL AMOUNT DUE" / "BALANCE THIS STATEMENT". One table per sheet.
  - **Output:** Only Charge Amount, Adjustment, Balance Due are extracted; values parsed as currency (leading `$`, commas stripped). Rows with any empty target column are skipped. Source tracking columns (Source Sheet, Source Workbook, Invoice Type) are added per row.
- **Transformations** (`backend/services/transformations/`) — `BannerBillingsCombiner` aggregates data from multiple sheets/workbooks into a single DataFrame and generates summary statistics (including invoice_type per sheet).
- **Reports** (`backend/services/reports/`) — `ExcelReportGenerator` creates formatted Excel with Summary sheet (includes Invoice Type) and Combined Data sheet (columns: Charge Amount, Adjustment, Balance Due, Source Sheet, Source Workbook, Invoice Type).
- **API** (`backend/api/clinical_trials.py`) — `POST /clinical-trials/process-billings` accepts one or more Excel files, returns downloadable report; `GET /clinical-trials/status` for health checks.
- **Frontend** (`frontend/modules/clinical_trials/`) — Upload page with drag-and-drop, Process button, and automatic report download. Mounted at `/clinicaltrialsupload`.
- **Wiring** — Router registered; separate Dash app created; "Clinical Trials Data Upload" button on welcome page (`/welcome`).

**Flow:** Upload Excel → processor extracts all tabs (by invoice type) → combiner aggregates → report generator creates workbook → direct download. No database writes (file-to-file only for now).

**Next Steps for Clinical Trials:**
- **Optional:** Extract metadata from outside the table (e.g. RESEARCH, KFS NO., IRB NO. in column A above the table) and include in metadata or report.
- Consider database persistence for clinical trials data in the future.

---

## Next 1–2 Steps

### Step 1: Implement Explicit Column Mapping System
**Priority:** High

**Tasks:**
1. Create column mapping configuration file (`backend/services/processors/column_mappings.py` or similar)
   - Define explicit source → target column mappings for each dataset type
   - Define columns to remove/exclude
   - Define data type specifications per column
2. Update each processor's `transform_rows()` method:
   - Replace generic `_map_column_names()` with explicit mapping lookup
   - Filter out unwanted columns
   - Apply data type conversions
3. Add helper methods to base processor for mapping/config access

**Files to Modify:**
- All 6 processor files (`rlogx_budgets_processor.py`, `rlogx_funding_processor.py`, etc.)
- `base_processor.py` (add helper methods)
- `utils.py` (add data type conversion utilities)
- New file: `column_mappings.py` (or integrate into processors)

### Step 2: Enhance Data Type Conversion
**Priority:** High

**Tasks:**
1. Add data type conversion utilities to `utils.py`:
   - `convert_to_int()`, `convert_to_float()`, `convert_to_bool()`, `convert_to_string()`
   - Handle None, NaN, empty strings appropriately
2. Update `write_to_database()` methods in all processors:
   - Apply data type conversions for all columns (not just dates)
   - Ensure proper type casting before database insertion

### Step 3: Clinical Trials — Optional Metadata Extraction
**Priority:** Low

**Status:** Table extraction is implemented (Hospital vs Professional, target columns Charge Amount / Adjustment / Balance Due, header and table-end detection).

**Optional tasks:**
1. Implement `extract_metadata_from_sheet()` to pull specific fields from above the table (e.g. RESEARCH, KFS NO., IRB NO. in column A).
2. Include extracted metadata in the Summary sheet or combined report.
3. Consider database persistence for clinical trials data (future enhancement).

---

## Known Open Questions

1. **Column Mapping Configuration Format:**
   - Should mappings be in a separate config file or embedded in each processor?
   - What format should the mapping file use? (Python dict, JSON, YAML?)

2. **Authentication & Authorization:**
   - When should RBAC be implemented? (Currently placeholder)
   - What authentication method? (Shibboleth headers, JWT tokens?)

3. **Database Initialization:**
   - Should `await init_db()` be uncommented in `app.py` startup?
   - Or rely on manual migrations?

4. **Upload Tracking:**
   - How should file IDs and batch IDs be generated?
   - What level of upload history tracking is needed?

5. **Future Features:**
   - Dashboard/visualization modules (mentioned in README but not started)
   - Data query/retrieval endpoints
   - Export functionality

6. **Data Quality:**
   - What validation rules need to be added beyond required columns?
   - How should duplicate records be handled?

7. **Clinical Trials / Banner Billings:**
   - What is the exact structure of the source Excel tabs (header rows, table location, metadata cells)?
   - Which columns/fields should be extracted from each tab?
   - Should clinical trials data be persisted to the database in the future?

---

## Why This Matters (Motivation Anchor)

This project matters because:

1. **Research Data Integrity:** Accurate, validated research data is critical for cancer center reporting, grant applications, and institutional metrics. Manual data entry errors can have significant downstream impacts.

2. **Efficiency:** Automating the data upload and validation process saves hours of manual work and reduces human error. The parallel processing capability allows bulk uploads that would be impractical manually.

3. **Foundation for Analytics:** This system provides the clean, structured data foundation needed for future dashboards, reports, and analytical tools that will help UACC leadership make data-driven decisions.

4. **Compliance & Reporting:** Many research institutions require accurate tracking and reporting of funding, publications, and membership data. This system ensures data quality and provides audit trails through upload metadata.

5. **Scalability:** As UACC grows and data volumes increase, having an automated, validated pipeline becomes essential rather than nice-to-have.

6. **Clinical Trials Billing:** The new Clinical Trials module automates the consolidation of Banner Billing data from partner-provided Excel workbooks (one bill per tab), reducing manual work for colleagues and providing a standardized, downloadable report.

**The current column mapping issue is blocking proper data quality** - fixing it is essential to ensure the right data gets stored correctly, which is the core value proposition of this system.

---

## Quick Reference

**Tech Stack:**
- Backend: FastAPI (Python)
- Frontend: Dash (Python)
- Database: MySQL (async via SQLAlchemy + asyncmy)
- File Processing: pandas

**Key Directories:**
- `backend/services/processors/` - Dataset processors (including `banner_billings_processor.py`)
- `backend/services/transformations/` - Data aggregation (Banner Billings combiner)
- `backend/services/reports/` - Excel report generation
- `backend/models/` - ORM models
- `backend/api/` - API endpoints (admin, clinical_trials)
- `frontend/modules/admin/` - Admin upload UI
- `frontend/modules/clinical_trials/` - Clinical Trials upload UI

**Key URLs:**
- `/welcome` - Landing page with links to both upload modules
- `/adminupload` - Admin Data Upload (research datasets)
- `/clinicaltrialsupload` - Clinical Trials Data Upload (Banner Billings)
- `/clinical-trials/process-billings` - API endpoint for Banner Billing processing

**Current Focus:** Column mapping and data type conversion fixes (admin); clinical trials table extraction implemented (optional: metadata extraction above table)
