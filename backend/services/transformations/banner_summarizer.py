"""
Summarizer for Banner Billings data.

This module produces aggregated summaries from combined billing data:
1. Study-level: by Study Name, Study Code, KFS No, IRB No, Invoice Date, Invoice Type
2. Account-level: by KFS No, Invoice Type, Invoice Date
"""
import logging
from typing import Dict, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Internal column names in combined DataFrame (from processor)
_COL_STUDY_NAME = "STUDY NAME"
_COL_STUDY_CODE = "STUDY CODE"
_COL_KFS_NO = "KFS NO"
_COL_IRB_NO = "IRB NO"
_COL_INVOICE_DATE = "invoice_date"
_COL_INVOICE_TYPE = "_invoice_type"
_COL_CHARGE_AMOUNT = "Charge Amount"
_COL_ADJUSTMENT = "Adjustment"
_COL_BALANCE_DUE = "Balance Due"

# Display column names for report output (title case, IRB/KFS/PI stay capitalized)
_DISPLAY_RENAME = {
    _COL_STUDY_NAME: "Study Name",
    _COL_STUDY_CODE: "Study Code",
    _COL_KFS_NO: "KFS No",
    _COL_IRB_NO: "IRB No",
    _COL_INVOICE_DATE: "Invoice Date",
    _COL_INVOICE_TYPE: "Invoice Type",
    _COL_CHARGE_AMOUNT: "Charge Amount",
    _COL_ADJUSTMENT: "Adjustment",
    _COL_BALANCE_DUE: "Balance Due",
}

_SUM_COLUMNS = [_COL_CHARGE_AMOUNT, _COL_ADJUSTMENT, _COL_BALANCE_DUE]


class BannerBillingsSummarizer:
    """
    Produces summary DataFrames from combined Banner Billings data.
    """

    @staticmethod
    def get_study_level_summary(df: pd.DataFrame) -> pd.DataFrame:
        """
        Group by Study Name, Study Code, KFS No, IRB No, Invoice Date, Invoice Type;
        sum Charge Amount, Adjustment, Balance Due.

        Args:
            df: Combined DataFrame from BannerBillingsCombiner

        Returns:
            Summary DataFrame with aggregated amounts (display column names)
        """
        group_cols = [
            _COL_STUDY_NAME,
            _COL_STUDY_CODE,
            _COL_KFS_NO,
            _COL_IRB_NO,
            _COL_INVOICE_DATE,
            _COL_INVOICE_TYPE,
        ]
        return BannerBillingsSummarizer._aggregate(df, group_cols)

    @staticmethod
    def get_account_level_summary(df: pd.DataFrame) -> pd.DataFrame:
        """
        Group by KFS No, Invoice Type, Invoice Date; sum Charge Amount,
        Adjustment, Balance Due.

        Args:
            df: Combined DataFrame from BannerBillingsCombiner

        Returns:
            Summary DataFrame with aggregated amounts (display column names)
        """
        group_cols = [_COL_KFS_NO, _COL_INVOICE_TYPE, _COL_INVOICE_DATE]
        return BannerBillingsSummarizer._aggregate(df, group_cols)

    @staticmethod
    def get_summaries(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Produce both summary DataFrames.

        Args:
            df: Combined DataFrame from BannerBillingsCombiner

        Returns:
            Tuple of (study_level_summary, account_level_summary)
        """
        study = BannerBillingsSummarizer.get_study_level_summary(df)
        account = BannerBillingsSummarizer.get_account_level_summary(df)
        return study, account

    @staticmethod
    def _aggregate(
        df: pd.DataFrame, group_cols: list
    ) -> pd.DataFrame:
        """
        Group by specified columns, sum numeric columns. Fill NaN in group
        columns for consistent grouping. Rename output to display names.

        Args:
            df: Combined DataFrame
            group_cols: Column names to group by

        Returns:
            Aggregated DataFrame with display column names
        """
        if df.empty:
            display_cols = [_DISPLAY_RENAME.get(c, c) for c in group_cols]
            display_cols.extend(["Charge Amount", "Adjustment", "Balance Due"])
            return pd.DataFrame(columns=display_cols)

        missing = [c for c in group_cols + _SUM_COLUMNS if c not in df.columns]
        if missing:
            logger.warning(
                f"Summarizer: missing columns {missing}, skipping aggregation"
            )
            display_cols = [_DISPLAY_RENAME.get(c, c) for c in group_cols]
            display_cols.extend(["Charge Amount", "Adjustment", "Balance Due"])
            return pd.DataFrame(columns=display_cols)

        df_work = df.copy()
        for col in group_cols:
            df_work[col] = df_work[col].fillna("").astype(str).str.strip()

        result = (
            df_work.groupby(group_cols, dropna=False)[_SUM_COLUMNS]
            .sum()
            .reset_index()
        )

        result = result.rename(columns=_DISPLAY_RENAME)
        logger.debug(f"Summarizer: produced {len(result)} aggregated rows")
        return result
