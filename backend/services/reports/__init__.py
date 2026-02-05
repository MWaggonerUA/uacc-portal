"""
Reports package for generating formatted output files.

This package contains modules for generating formatted Excel workbooks
and other report formats from processed data.
"""
from backend.services.reports.excel_generator import ExcelReportGenerator

__all__ = ['ExcelReportGenerator']
