"""
Utility functions for dataset processors.

This module provides helper functions for common data transformation tasks,
such as date parsing, value normalization, etc.
"""
import logging
import re
from typing import Optional, Any
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_date(value: Any) -> Optional[str]:
    """
    Parse a date value from various formats and return ISO format string.
    
    Handles multiple date formats commonly found in Excel/CSV files:
    - ISO format: '2024-01-15', '2024-01-15 10:30:00'
    - US format: '01/15/2024', '1/15/2024', '01-15-2024'
    - European format: '15/01/2024', '15-01-2024'
    - Year-month-day with month name: '2022 Mar 11', '2022 March 11'
    - Year and month: '2022 Jan', '2022 January' (defaults to 1st day)
    - Year only: '2019', '2022' (defaults to January 1st)
    - Excel serial dates (numbers)
    - String dates with various separators and formats
    - Already parsed datetime objects
    
    For incomplete dates:
    - Missing month defaults to January (month 1)
    - Missing day defaults to the 1st day of the month
    
    Returns None if the date cannot be parsed (for optional date fields).
    Returns ISO format string (YYYY-MM-DD) if successful.
    
    Args:
        value: Date value to parse (can be string, number, datetime, etc.)
        
    Returns:
        ISO format date string (YYYY-MM-DD) or None if parsing fails
        
    Examples:
        >>> parse_date('2024-01-15')
        '2024-01-15'
        >>> parse_date('01/15/2024')
        '2024-01-15'
        >>> parse_date('15/01/2024')
        '2024-01-15'
        >>> parse_date('2022 Mar 11')
        '2022-03-11'
        >>> parse_date('2022 Jan')
        '2022-01-01'
        >>> parse_date('2019')
        '2019-01-01'
        >>> parse_date(45321)  # Excel serial date
        '2024-01-15'
        >>> parse_date(None)
        None
        >>> parse_date('')
        None
        >>> parse_date('invalid')
        None
    """
    # Handle None, empty strings, and NaN values
    if value is None:
        return None
    
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ('', 'nan', 'none', 'null', 'n/a', 'na'):
            return None
    
    # Check if already a pandas Timestamp or datetime object
    if isinstance(value, (pd.Timestamp, datetime)):
        try:
            return value.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return None
    
    # Check if it's a numeric value (Excel serial date)
    if isinstance(value, (int, float)):
        try:
            # Excel serial dates start from 1900-01-01 (but Excel incorrectly treats 1900 as a leap year)
            # pandas handles this conversion correctly
            parsed = pd.to_datetime(value, origin='1899-12-30', unit='D')
            return parsed.strftime('%Y-%m-%d')
        except (ValueError, OverflowError, OSError):
            # If it's not a valid serial date, try treating as timestamp
            try:
                parsed = pd.to_datetime(value, unit='s', errors='coerce')
                if pd.notna(parsed):
                    return parsed.strftime('%Y-%m-%d')
            except (ValueError, OverflowError, OSError):
                pass
            return None
    
    # Handle string dates with special formats (publications data)
    if isinstance(value, str):
        value_str = value.strip()
        
        # Pattern 1: Year only (e.g., "2019", "2022")
        # Match 4-digit year at start/end of string
        year_only_match = re.match(r'^(\d{4})$', value_str)
        if year_only_match:
            year = int(year_only_match.group(1))
            # Validate year is reasonable (between 1900 and 2100)
            if 1900 <= year <= 2100:
                return f"{year:04d}-01-01"  # Default to January 1st
        
        # Pattern 2: Year and month name (e.g., "2022 Jan", "2022 January", "2022Mar")
        # Match: 4-digit year, optional space, month name (abbrev or full)
        year_month_match = re.match(
            r'^(\d{4})\s*([A-Za-z]+)$',
            value_str,
            re.IGNORECASE
        )
        if year_month_match:
            year = int(year_month_match.group(1))
            month_str = year_month_match.group(2).lower()
            
            # Map month names to numbers
            month_map = {
                'jan': 1, 'january': 1,
                'feb': 2, 'february': 2,
                'mar': 3, 'march': 3,
                'apr': 4, 'april': 4,
                'may': 5,
                'jun': 6, 'june': 6,
                'jul': 7, 'july': 7,
                'aug': 8, 'august': 8,
                'sep': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11,
                'dec': 12, 'december': 12
            }
            
            # Try to match month (check full name first, then abbreviation)
            month = None
            for month_key, month_num in month_map.items():
                if month_str.startswith(month_key[:3]):  # Match first 3 chars for abbreviations
                    month = month_num
                    break
            
            if month and 1900 <= year <= 2100:
                return f"{year:04d}-{month:02d}-01"  # Default to 1st day
        
        # Pattern 3: Year, month name, and day (e.g., "2022 Mar 11", "2022 March 11", "2022Mar11")
        # Match: 4-digit year, optional space, month name, optional space, 1-2 digit day
        year_month_day_match = re.match(
            r'^(\d{4})\s*([A-Za-z]+)\s*(\d{1,2})$',
            value_str,
            re.IGNORECASE
        )
        if year_month_day_match:
            year = int(year_month_day_match.group(1))
            month_str = year_month_day_match.group(2).lower()
            day = int(year_month_day_match.group(3))
            
            # Map month names to numbers (same as above)
            month_map = {
                'jan': 1, 'january': 1,
                'feb': 2, 'february': 2,
                'mar': 3, 'march': 3,
                'apr': 4, 'april': 4,
                'may': 5,
                'jun': 6, 'june': 6,
                'jul': 7, 'july': 7,
                'aug': 8, 'august': 8,
                'sep': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11,
                'dec': 12, 'december': 12
            }
            
            # Try to match month
            month = None
            for month_key, month_num in month_map.items():
                if month_str.startswith(month_key[:3]):
                    month = month_num
                    break
            
            if month and 1900 <= year <= 2100 and 1 <= day <= 31:
                try:
                    # Validate the date (e.g., Feb 30 is invalid)
                    test_date = datetime(year, month, day)
                    return test_date.strftime('%Y-%m-%d')
                except ValueError:
                    # Invalid date (e.g., Feb 30), return None
                    logger.debug(f"Invalid date: {year}-{month}-{day}")
                    return None
    
    # Try parsing as string date with pandas (handles many formats automatically)
    try:
        # pandas to_datetime is very flexible and handles many formats
        # It tries multiple parsing strategies automatically
        # Note: infer_datetime_format is deprecated, pandas now does this by default
        parsed = pd.to_datetime(value, errors='coerce')
        
        if pd.notna(parsed):
            return parsed.strftime('%Y-%m-%d')
    except (ValueError, TypeError, OverflowError, OSError) as e:
        logger.debug(f"Failed to parse date value '{value}': {e}")
        return None
    
    # If all parsing attempts failed, return None
    return None

