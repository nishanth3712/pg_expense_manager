"""Financial calculation utilities for rental dashboard.

CALCULATION FORMULAS:
====================

MONTHLY CALCULATIONS:
- Total Rent (Revenue)    = Sum of all Income transactions
- Expenses                = Sum of all Expense transactions
- Net Profit              = Total Rent - Expenses
                           (Operational profit before owner's draw)
- Profit Deducted         = Owner's draw/withdrawal (manual input)
- Opening Balance         = Starting balance for the month (manual input)
- Net Balance             = Opening Balance + Total Rent - Expenses - Profit Deducted
                           (Total cash position)

YEARLY CALCULATIONS:
- Opening Balance (Month) = Previous Month's Closing Balance
                           (or manual override from config)
- Net Profit (Month)      = Revenue - Expenses
- Closing Balance         = Opening Balance + Net Profit - Profit Deducted
- Annual Opening          = First month's Opening Balance
- Annual Closing          = Last month's Closing Balance

RELATIONSHIPS:
==============
Net Profit      ← Revenue - Expenses
Closing Balance ← Opening Balance + Net Profit - Profit Deducted
Next Month OB   ← Previous Month's Closing Balance
"""
from typing import Dict, List, Any
import pandas as pd


def calculate_yaxis_max(values: list, buffer_percent: float = 0.2) -> float:
    """
    Calculate Y-axis max with buffer for charts.

    Args:
        values: List of numeric values
        buffer_percent: Buffer percentage (default 20%)

    Returns:
        Max value with buffer applied, rounded to nice number
    """
    if not values or all(v == 0 for v in values):
        return 100  # Default minimum

    max_val = max(values)
    if max_val <= 0:
        return 100

    # Add buffer
    buffered = max_val * (1 + buffer_percent)

    # Round to nice number (next significant division)
    magnitude = 10 ** (len(str(int(buffered))) - 1)
    return ((int(buffered) // magnitude) + 1) * magnitude


def calculate_monthly_net(opening_balance: float, rent_received: float,
                          total_expenses: float, profit_deducted: float) -> float:
    """
    Calculate net balance for a month.

    Formula: Net = (Opening Balance + Total Rent) - Total Expenses - Profit Deducted

    Args:
        opening_balance: Opening balance for the month
        rent_received: Total rent received (cash + bank)
        total_expenses: Total expenses for the month
        profit_deducted: Profit/withdrawals deducted

    Returns:
        Net balance amount
    """
    return (opening_balance + rent_received) - total_expenses - profit_deducted


def aggregate_by_category(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Aggregate transactions by category.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Dictionary mapping category to total amount
    """
    totals = {}
    for txn in transactions:
        category = txn.get("Category", "Misc")
        amount = float(txn.get("Amount", 0))
        totals[category] = totals.get(category, 0) + amount
    return totals


def calculate_kpis(df: pd.DataFrame, opening_balance: float,
                   profit_deducted: float) -> Dict[str, float]:
    """
    Calculate KPIs for a month's data.

    Args:
        df: DataFrame with transactions for the month
        opening_balance: Opening balance for the month
        profit_deducted: Profit deducted for the month

    Returns:
        Dictionary with calculated KPIs
    """
    if df.empty:
        return {
            "opening_balance": opening_balance,
            "rent_cash": 0.0,
            "rent_bank": 0.0,
            "rent_total": 0.0,
            "expenses": 0.0,
            "profit_deducted": profit_deducted,
            "net_balance": calculate_monthly_net(opening_balance, 0, 0, profit_deducted)
        }

    # Filter income and expenses
    income_df = df[df["Type"] == "Income"]
    expense_df = df[df["Type"] == "Expense"]

    # Calculate rent by mode
    rent_cash = income_df[income_df["Mode"] == "Cash"]["Amount"].sum()
    rent_bank = income_df[income_df["Mode"] == "Bank"]["Amount"].sum()
    rent_total = rent_cash + rent_bank

    # Calculate expenses
    expenses = expense_df["Amount"].sum()

    # Calculate net balance (includes opening balance and all deductions)
    # Formula: Opening Balance + Rent - Expenses - Profit Deducted
    net = calculate_monthly_net(opening_balance, rent_total, expenses, profit_deducted)

    # Calculate net profit (simple: revenue - expenses)
    # This is the profit before owner's draw/profit deduction
    net_profit = rent_total - expenses

    return {
        "opening_balance": opening_balance,
        "rent_cash": rent_cash,
        "rent_bank": rent_bank,
        "rent_total": rent_total,
        "expenses": expenses,
        "profit_deducted": profit_deducted,
        "net_balance": net,
        "net_profit": net_profit
    }


def calculate_yearly_summary(monthly_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Calculate yearly summary from monthly data with Opening/Closing Balance.

    Args:
        monthly_data: List of dictionaries with month_name, revenue, expenses,
                     profit_deducted, opening_balance

    Returns:
        DataFrame with yearly summary including Opening Balance and Closing Balance
    """
    if not monthly_data:
        return pd.DataFrame(columns=[
            "Month", "Opening Balance", "Revenue", "Expenses",
            "Net Profit", "Profit Deducted", "Closing Balance"
        ])

    rows = []
    prev_closing_balance = None

    for i, data in enumerate(monthly_data):
        month_name = data.get("month_name", "")
        revenue = data.get("revenue", 0)
        expenses = data.get("expenses", 0)
        profit_deducted = data.get("profit_deducted", 0)

        # Opening balance: use provided value or previous month's closing
        if i == 0 or data.get("opening_balance", 0) != 0:
            opening_balance = data.get("opening_balance", 0)
        else:
            # Use previous month's closing balance
            opening_balance = prev_closing_balance if prev_closing_balance is not None else 0

        # Net Profit = Revenue - Expenses (operational profit)
        net_profit = revenue - expenses
        # Closing Balance = Opening + Net Profit - Profit Deducted
        closing_balance = opening_balance + net_profit - profit_deducted

        rows.append({
            "Month": month_name,
            "Opening Balance": opening_balance,
            "Revenue": revenue,
            "Expenses": expenses,
            "Net Profit": net_profit,
            "Profit Deducted": profit_deducted,
            "Closing Balance": closing_balance
        })

        prev_closing_balance = closing_balance

    return pd.DataFrame(rows)


def format_currency(amount: float) -> str:
    """Format amount as Indian Rupees."""
    return f"₹{amount:,.2f}"


def format_date(date_obj) -> str:
    """Format date as DD/MM/YYYY."""
    if hasattr(date_obj, "strftime"):
        return date_obj.strftime("%d/%m/%Y")
    return str(date_obj)
