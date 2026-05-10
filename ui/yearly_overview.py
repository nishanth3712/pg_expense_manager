"""Yearly overview UI component for rental dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from sheets_client import (
    get_gsheets_connection, get_spreadsheet, get_or_create_config_sheet,
    get_monthly_config, get_month_transactions, get_available_years
)
from calculator import calculate_yearly_summary, format_currency, calculate_yaxis_max


def get_monthly_data_for_year(spreadsheet, year: int) -> list:
    """
    Collect monthly data for a given year.

    Args:
        spreadsheet: Google Spreadsheet object
        year: Year to collect data for

    Returns:
        List of monthly data dictionaries
    """
    from sheets_client import get_all_months, get_or_create_month_sheet

    all_months = get_all_months(spreadsheet)
    monthly_data = []

    # Month name to number mapping for sorting
    month_order = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    for month_name in all_months:
        # Check if this month belongs to the selected year
        if not month_name.endswith(f"_{year}"):
            continue

        try:
            # Get month sheet
            month_sheet = get_or_create_month_sheet(spreadsheet, month_name)

            # Get transactions
            df = get_month_transactions(month_sheet)

            # Calculate totals
            revenue = 0.0
            expenses = 0.0

            if not df.empty:
                revenue = df[df["Type"] == "Income"]["Amount"].sum()
                expenses = df[df["Type"] == "Expense"]["Amount"].sum()

            # Get config for opening balance and profit deducted
            config_sheet = get_or_create_config_sheet(spreadsheet)
            config = get_monthly_config(config_sheet, month_name)
            opening_balance = config.get("opening_balance", 0.0)
            profit_deducted = config.get("profit_deducted", 0.0)

            # Extract month name without year
            display_name = month_name.replace(f"_{year}", "")

            monthly_data.append({
                "month_name": display_name,
                "month_num": month_order.get(display_name, 99),
                "year": year,
                "revenue": revenue,
                "expenses": expenses,
                "opening_balance": opening_balance,
                "profit_deducted": profit_deducted
            })

        except Exception as e:
            st.warning(f"Could not load data for {month_name}: {str(e)}")
            continue

    # Sort by month number
    monthly_data.sort(key=lambda x: x["month_num"])

    return monthly_data


def render_year_selector(available_years: list) -> int:
    """Render year selector dropdown."""
    if not available_years:
        # Default to current year if no data yet
        return datetime.now().year

    current_year = datetime.now().year
    default_idx = available_years.index(current_year) if current_year in available_years else 0

    selected_year = st.selectbox(
        "📅 Select Year",
        options=available_years,
        index=min(default_idx, len(available_years) - 1)
    )
    return selected_year


def render_yearly_table(summary_df: pd.DataFrame):
    """Render yearly summary table with Opening/Closing Balance."""
    st.subheader("📊 Yearly Summary Table")

    if summary_df.empty:
        st.info("No data available for this year.")
        return

    # Format currency columns
    display_df = summary_df.copy()
    currency_columns = [
        "Opening Balance", "Revenue", "Expenses",
        "Net Profit", "Profit Deducted", "Closing Balance"
    ]
    for col in currency_columns:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_currency)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Calculate and display totals
    opening_balance_first = summary_df["Opening Balance"].iloc[0] if not summary_df.empty else 0
    closing_balance_last = summary_df["Closing Balance"].iloc[-1] if not summary_df.empty else 0
    total_revenue = summary_df["Revenue"].sum()
    total_expenses = summary_df["Expenses"].sum()
    total_net = summary_df["Net Profit"].sum()
    total_profit_deducted = summary_df["Profit Deducted"].sum()

    st.divider()
    st.subheader("📈 Annual Totals")

    # Styled container for better visibility
    st.markdown("""
    <style>
    .annual-totals {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #4a90c2;
    }
    .annual-totals [data-testid="stMetricLabel"] {
        color: #a0d2ff !important;
        font-weight: 500 !important;
    }
    .annual-totals [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="annual-totals">', unsafe_allow_html=True)

        # 3x2 grid: Opening | Revenue | Expenses
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            st.metric("Opening Balance", format_currency(opening_balance_first), label_visibility="visible")
        with r1c2:
            st.metric("Revenue", format_currency(total_revenue), label_visibility="visible")
        with r1c3:
            st.metric("Expenses", format_currency(total_expenses), label_visibility="visible")

        # Second row: Net Profit | Profit Out | Closing
        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            st.metric("Net Profit", format_currency(total_net), label_visibility="visible")
        with r2c2:
            st.metric("Profit Out", format_currency(total_profit_deducted), label_visibility="visible")
        with r2c3:
            st.metric("Closing Balance", format_currency(closing_balance_last), label_visibility="visible")

        st.markdown('</div>', unsafe_allow_html=True)


def render_profit_chart(summary_df: pd.DataFrame):
    """Render profit over time line chart."""
    st.subheader("📈 Profit Over Time")

    if summary_df.empty:
        st.info("No data available for chart.")
        return

    # Calculate y-axis max with 20% buffer
    all_values = (
        summary_df["Revenue"].tolist() +
        summary_df["Expenses"].tolist() +
        summary_df["Net Profit"].tolist()
    )
    y_max = calculate_yaxis_max(all_values, buffer_percent=0.2)

    fig = go.Figure()

    # Add revenue line
    fig.add_trace(go.Scatter(
        x=summary_df["Month"],
        y=summary_df["Revenue"],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#2ecc71', width=2)
    ))

    # Add expenses line
    fig.add_trace(go.Scatter(
        x=summary_df["Month"],
        y=summary_df["Expenses"],
        mode='lines+markers',
        name='Expenses',
        line=dict(color='#e74c3c', width=2)
    ))

    # Add net profit line
    fig.add_trace(go.Scatter(
        x=summary_df["Month"],
        y=summary_df["Net Profit"],
        mode='lines+markers',
        name='Net Profit',
        line=dict(color='#3498db', width=3)
    ))

    fig.update_layout(
        title="Monthly Trends",
        xaxis_title="Month",
        yaxis=dict(
            title="Amount (₹)",
            range=[0, y_max]
        ),
        hovermode='x unified',
        height=380,
        margin=dict(l=40, r=20, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_expense_breakdown_chart(monthly_data: list):
    """Render aggregated expense breakdown pie chart."""
    from sheets_client import get_all_months, get_or_create_month_sheet

    st.subheader("📊 Annual Expense Breakdown")

    try:
        conn = get_gsheets_connection()
        spreadsheet = get_spreadsheet(conn)

        # Aggregate expenses by category across all months in selected year
        category_totals = {}

        for month_data in monthly_data:
            month_full_name = f"{month_data['month_name']}_{month_data['year']}"
            try:
                month_sheet = get_or_create_month_sheet(spreadsheet, month_full_name)
                df = get_month_transactions(month_sheet)

                if not df.empty:
                    expense_df = df[df["Type"] == "Expense"]
                    for _, row in expense_df.iterrows():
                        category = row.get("Category", "Misc")
                        amount = float(row.get("Amount", 0))
                        category_totals[category] = category_totals.get(category, 0) + amount
            except Exception:
                continue

        if not category_totals:
            st.info("No expense data available for breakdown.")
            return

        # Create pie chart
        fig = px.pie(
            values=list(category_totals.values()),
            names=list(category_totals.keys()),
            title="Expenses by Category",
            hole=0.4
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    except Exception as e:
        st.warning(f"Could not render expense breakdown: {str(e)}")


def render_yearly_overview():
    """Main yearly overview rendering function."""
    st.title("📅 Yearly View")

    try:
        # Get connection and spreadsheet
        conn = get_gsheets_connection()
        spreadsheet = get_spreadsheet(conn)

        # Get available years
        available_years = get_available_years(spreadsheet)

        # Year selector
        selected_year = render_year_selector(available_years)

        st.divider()

        # Get monthly data for selected year
        monthly_data = get_monthly_data_for_year(spreadsheet, selected_year)

        if not monthly_data:
            st.info(f"📭 No data available for {selected_year}. Start adding transactions to see your yearly overview!")
            return

        # Calculate yearly summary
        summary_df = calculate_yearly_summary(monthly_data)

        # Render table
        render_yearly_table(summary_df)

        st.divider()

        # Render profit chart
        render_profit_chart(summary_df)

        st.divider()

        # Render expense breakdown
        render_expense_breakdown_chart(monthly_data)

    except Exception as e:
        st.error(f"❌ Error loading yearly overview: {str(e)}")
        st.info("Please check your Google Sheets connection and credentials.")
