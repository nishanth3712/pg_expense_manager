"""Google Sheets client for rental dashboard."""
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials

# Sheet headers for monthly sheets
MONTHLY_HEADERS = ["Date", "Category", "Description", "Type", "Mode", "Amount"]

# Expense categories
EXPENSE_CATEGORIES = [
    "Maintenance",
    "Utilities",
    "Tax",
    "Grocery",
    "Salaries",
    "Misc"
]


def clear_data_cache():
    """Clear cached data to force refresh after modifications."""
    get_month_transactions.clear()
    get_monthly_config.clear()
    get_all_months.clear()


@st.cache_resource(ttl=3600)
def get_gsheets_connection():
    """Get Google Sheets connection using gspread directly."""
    try:
        # Get credentials from secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        st.info("Please ensure credentials are configured in .streamlit/secrets.toml")
        raise


@st.cache_resource(ttl=3600)
def get_spreadsheet(_conn) -> Any:
    """Get spreadsheet by ID from secrets."""
    try:
        spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "")
        if not spreadsheet_id:
            raise ValueError("SPREADSHEET_ID not found in secrets")
        return _conn.open_by_key(spreadsheet_id)
    except Exception as e:
        st.error(f"Failed to open spreadsheet: {str(e)}")
        raise


def get_or_create_month_sheet(spreadsheet, month_year: str) -> Any:
    """
    Get or create a sheet for the given month.

    Args:
        spreadsheet: Google Spreadsheet object
        month_year: Month-year string (e.g., "May_2026")

    Returns:
        Worksheet object for the month
    """
    try:
        try:
            worksheet = spreadsheet.worksheet(month_year)
            return worksheet
        except:
            # Sheet doesn't exist, create it
            worksheet = spreadsheet.add_worksheet(title=month_year, rows=1000, cols=6)
            worksheet.append_row(MONTHLY_HEADERS)
            # Format header row
            worksheet.format("A1:F1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            return worksheet
    except Exception as e:
        st.error(f"Error accessing sheet '{month_year}': {str(e)}")
        raise


def get_or_create_config_sheet(spreadsheet) -> Any:
    """
    Get or create the Monthly Config sheet.

    Args:
        spreadsheet: Google Spreadsheet object

    Returns:
        Worksheet object for config
    """
    try:
        try:
            worksheet = spreadsheet.worksheet("Monthly Config")
            return worksheet
        except:
            # Create config sheet
            worksheet = spreadsheet.add_worksheet(title="Monthly Config", rows=100, cols=3)
            worksheet.append_row(["Month", "Opening Balance", "Profit Deducted"])
            worksheet.format("A1:C1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            return worksheet
    except Exception as e:
        st.error(f"Error accessing config sheet: {str(e)}")
        raise


@st.cache_data(ttl=300)
def get_monthly_config(_worksheet, month_year: str) -> Dict[str, float]:
    """
    Get opening balance and profit deducted for a month.

    Args:
        _worksheet: Config worksheet
        month_year: Month-year string

    Returns:
        Dictionary with opening_balance and profit_deducted
    """
    try:
        records = _worksheet.get_all_records()
        for record in records:
            if record.get("Month") == month_year:
                return {
                    "opening_balance": float(record.get("Opening Balance", 0) or 0),
                    "profit_deducted": float(record.get("Profit Deducted", 0) or 0)
                }
        return {"opening_balance": 0.0, "profit_deducted": 0.0}
    except Exception as e:
        st.warning(f"Could not read config for {month_year}: {str(e)}")
        return {"opening_balance": 0.0, "profit_deducted": 0.0}


def set_monthly_config(worksheet, month_year: str,
                       opening_balance: float, profit_deducted: float):
    """
    Set opening balance and profit deducted for a month.

    Args:
        worksheet: Config worksheet
        month_year: Month-year string
        opening_balance: Opening balance value
        profit_deducted: Profit deducted value
    """
    try:
        records = worksheet.get_all_records()
        for idx, record in enumerate(records, start=2):  # Header is row 1
            if record.get("Month") == month_year:
                worksheet.update_cell(idx, 2, opening_balance)
                worksheet.update_cell(idx, 3, profit_deducted)
                return

        # Month not found, append new row
        worksheet.append_row([month_year, opening_balance, profit_deducted])

        clear_data_cache()  # Clear cache after modification
    except Exception as e:
        st.error(f"Error saving config for {month_year}: {str(e)}")
        raise


@st.cache_data(ttl=120)
def get_month_transactions(_worksheet) -> pd.DataFrame:
    """
    Get all transactions for a month.

    Args:
        _worksheet: Monthly worksheet

    Returns:
        DataFrame with transactions
    """
    try:
        records = _worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=MONTHLY_HEADERS)
        df = pd.DataFrame(records)
        # Ensure Amount is numeric
        if "Amount" in df.columns:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.warning(f"Could not read transactions: {str(e)}")
        return pd.DataFrame(columns=MONTHLY_HEADERS)


def add_transaction(worksheet, date: str, category: str, description: str,
                    txn_type: str, mode: str, amount: float):
    """
    Add a transaction to the monthly sheet.

    Args:
        worksheet: Monthly worksheet
        date: Date string (DD/MM/YYYY)
        category: Transaction category
        description: Transaction description
        txn_type: "Income" or "Expense"
        mode: "Cash" or "Bank"
        amount: Transaction amount
    """
    try:
        worksheet.append_row([date, category, description, txn_type, mode, amount])
        clear_data_cache()  # Clear cache after modification
    except Exception as e:
        st.error(f"Error adding transaction: {str(e)}")
        raise


def delete_transaction(worksheet, row_index: int):
    """
    Delete a transaction by row index.

    Args:
        worksheet: Monthly worksheet
        row_index: Row index to delete (1-based, including header)
    """
    try:
        worksheet.delete_row(row_index)
    except Exception as e:
        st.error(f"Error deleting transaction: {str(e)}")
        raise


@st.cache_data(ttl=300)
def get_all_months(_spreadsheet) -> List[str]:
    """
    Get list of all month sheets in the spreadsheet.

    Args:
        spreadsheet: Google Spreadsheet object

    Returns:
        List of month sheet names (excluding config sheets)
    """
    try:
        worksheets = _spreadsheet.worksheets()
        months = []
        for ws in worksheets:
            title = ws.title
            # Skip config sheets
            if title in ["Monthly Config"]:
                continue
            # Check if title matches month_year pattern
            if "_" in title:
                months.append(title)
        return sorted(months)
    except Exception as e:
        st.error(f"Error listing sheets: {str(e)}")
        return []


def get_available_years(spreadsheet) -> List[int]:
    """
    Get list of available years from month sheets.

    Args:
        spreadsheet: Google Spreadsheet object

    Returns:
        List of years as integers
    """
    months = get_all_months(spreadsheet)
    years = set()
    for month in months:
        parts = month.split("_")
        if len(parts) >= 2:
            try:
                year = int(parts[-1])
                years.add(year)
            except ValueError:
                continue
    return sorted(list(years), reverse=True)
