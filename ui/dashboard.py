"""Dashboard UI component for rental dashboard."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from sheets_client import (
    get_gsheets_connection, get_spreadsheet, get_or_create_month_sheet,
    get_or_create_config_sheet, get_monthly_config, set_monthly_config,
    get_month_transactions, add_transaction, MONTHLY_HEADERS, EXPENSE_CATEGORIES
)
from calculator import calculate_kpis, format_currency, format_date


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


def render_month_selector(all_months: list, current_month: str) -> str:
    """Render month selector with year/month pickers (calendar style)."""
    from datetime import datetime
    from calendar import month_name

    now = datetime.now()
    current_year = now.year

    st.markdown("##### 📅 Select Month")

    # Force side-by-side layout even on mobile
    st.markdown("""
    <style>
    .month-selector-row {
        display: flex;
        flex-direction: row !important;
        gap: 8px;
    }
    .month-selector-row > div {
        flex: 1;
        min-width: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        default_year = st.session_state.get("selected_year", current_year)
        year_options = list(range(2020, current_year + 3))
        default_index = year_options.index(default_year) if default_year in year_options else 0

        year = st.selectbox(
            "Year",
            options=year_options,
            index=default_index,
            key="year_selector"
        )

    with col2:
        default_month = st.session_state.get("selected_month_num", now.month)

        month_names = [month_name[i] for i in range(1, 13)]
        month = st.selectbox(
            "Month",
            options=range(1, 13),
            format_func=lambda x: month_names[x-1],
            index=default_month - 1,
            key="month_selector"
        )

    # Store for next render
    st.session_state.selected_year = year
    st.session_state.selected_month_num = month

    return f"{month_name[month]}_{year}"


def render_kpi_cards(kpis: dict):
    """Render KPI metric cards - 3 in a horizontal row."""
    st.markdown("##### 💰 Monthly Metrics")

    # 3 metrics in a single row
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Rent", format_currency(kpis["rent_total"]))
    with m2:
        st.metric("Expenses", format_currency(kpis["expenses"]))
    with m3:
        st.metric("Net Profit", format_currency(kpis["net_profit"]))


def render_income_expense_chart(kpis: dict):
    """Render bar chart comparing income vs expenses - mobile optimized."""
    # Calculate y-axis max with 20% buffer
    y_max = calculate_yaxis_max([kpis["rent_total"], kpis["expenses"]], buffer_percent=0.2)

    fig = go.Figure(data=[
        go.Bar(
            name='Income',
            x=['Income'],
            y=[kpis["rent_total"]],
            marker_color='#2ecc71',
            text=[f'₹{kpis["rent_total"]:,.0f}'],
            textposition='outside'
        ),
        go.Bar(
            name='Expenses',
            x=['Expenses'],
            y=[kpis["expenses"]],
            marker_color='#e74c3c',
            text=[f'₹{kpis["expenses"]:,.0f}'],
            textposition='outside'
        )
    ])

    fig.update_layout(
        title="Income vs Expenses",
        barmode='group',
        yaxis=dict(
            title="Amount (₹)",
            range=[0, y_max]
        ),
        showlegend=True,
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_opening_balance_section(config_sheet, month_year: str):
    """Render opening balance section at top of page."""
    config = get_monthly_config(config_sheet, month_year)

    # Opening Balance section
    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            opening_balance = st.number_input(
                "Opening Balance (₹)",
                min_value=0.0,
                value=float(config["opening_balance"]),
                step=1000.0,
                format="%.2f",
                key="opening_balance_input"
            )
        with col2:
            if st.button("💾 Save", use_container_width=True, key="save_opening"):
                try:
                    set_monthly_config(config_sheet, month_year, opening_balance, config["profit_deducted"])
                    st.success("✅ Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def render_profit_deducted_section(config_sheet, month_year: str):
    """Render profit deducted section at bottom of page."""
    config = get_monthly_config(config_sheet, month_year)

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            profit_deducted = st.number_input(
                "Profit Deducted (₹)",
                min_value=0.0,
                value=float(config["profit_deducted"]),
                step=1000.0,
                format="%.2f",
                key="profit_deducted_input"
            )
        with col2:
            if st.button("💾 Save", use_container_width=True, key="save_profit"):
                try:
                    set_monthly_config(config_sheet, month_year, config["opening_balance"], profit_deducted)
                    st.success("✅ Saved!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def render_transactions_table(df: pd.DataFrame, month_sheet):
    """Render transactions table - mobile optimized."""
    if df.empty:
        st.info("No transactions this month.")
        return

    st.subheader(f"📋 Transactions ({len(df)})")

    # Format dataframe for display - show fewer columns on mobile
    display_df = df.copy()
    display_df["Amount"] = display_df["Amount"].apply(lambda x: format_currency(float(x)))

    # Show condensed view for mobile
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Amount": st.column_config.TextColumn("Amount", width="small"),
        }
    )

    # CSV download - full width button for mobile
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"txns_{datetime.now().strftime('%b_%Y')}.csv",
        mime="text/csv",
        use_container_width=True
    )


@st.dialog(title="💵 Add Income", width="small")
def render_quick_income_form(month_sheet):
    """Quick income form - dialog/modal layout."""
    c1, c2 = st.columns(2)
    with c1:
        income_date = st.date_input("Date", value=datetime.now(), format="DD/MM/YYYY")
        income_mode = st.selectbox("Mode", options=["Cash", "Bank"], index=1)
    with c2:
        income_amount = st.number_input("Amount (₹)", min_value=0.0, step=1000.0, format="%.2f")

    income_description = st.text_input("Description", value="Monthly Rent")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("✅ Add Income", type="primary", use_container_width=True):
            if income_amount <= 0:
                st.error("Amount must be greater than 0")
            else:
                try:
                    date_str = income_date.strftime("%d/%m/%Y")
                    add_transaction(month_sheet, date_str, "Rent", income_description, "Income", income_mode, income_amount)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with btn_col2:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            st.rerun()


@st.dialog(title="💸 Add Expense", width="small")
def render_quick_expense_form(month_sheet):
    """Quick expense form - dialog/modal layout."""
    c1, c2 = st.columns(2)
    with c1:
        expense_date = st.date_input("Date", value=datetime.now(), key="exp_date", format="DD/MM/YYYY")
        expense_category = st.selectbox("Category", options=EXPENSE_CATEGORIES, index=0)
    with c2:
        expense_mode = st.selectbox("Payment Mode", options=["Cash", "Bank"], key="exp_mode", index=1)
        expense_amount = st.number_input("Amount (₹)", min_value=0.0, key="exp_amt", step=100.0, format="%.2f")

    expense_description = st.text_input("Description", placeholder="e.g., Electricity bill")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("✅ Add Expense", type="primary", use_container_width=True):
            if expense_amount <= 0:
                st.error("Amount must be greater than 0")
            elif not expense_description.strip():
                st.error("Please provide a description")
            else:
                try:
                    date_str = expense_date.strftime("%d/%m/%Y")
                    add_transaction(month_sheet, date_str, expense_category, expense_description, "Expense", expense_mode, expense_amount)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with btn_col2:
        if st.button("❌ Cancel", type="secondary", use_container_width=True):
            st.rerun()


def render_dashboard():
    """Main dashboard rendering function - now called Overview."""
    st.title("📊 Overview")

    # Inject comprehensive CSS for styling all dashboard elements
    st.markdown("""
    <style>
    /* Hide number input spinners */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    input[type="number"] {
        -moz-appearance: textfield !important;
    }

    /* Metric cards styling - Dark themed */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #60a5fa !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: bold !important;
    }

    /* Quick Action Button Styling - Income (Green) - target by key class */
    [class*="st-key-btn_add_income"] button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: white !important;
        border: 2px solid #34d399 !important;
        font-weight: 700 !important;
    }

    /* Quick Action Button Styling - Expense (Red) - target by key class */
    [class*="st-key-btn_add_expense"] button {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        color: white !important;
        border: 2px solid #f87171 !important;
        font-weight: 700 !important;
    }

    /* Hide Opening Balance and Profit Deducted number input labels */
    [class*="st-key-opening_balance_input"] label,
    [class*="st-key-profit_deducted_input"] label {
        display: none !important;
    }

    /* Hide number input spin buttons (the +/- buttons inside stNumberInput) */
    .stNumberInput button {
        display: none !important;
    }

    /* Style Save buttons for Opening Balance and Profit Deducted */
    [class*="st-key-save_opening"] button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: white !important;
        border: 2px solid #34d399 !important;
        font-weight: 700 !important;
    }
    [class*="st-key-save_profit"] button {
        background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%) !important;
        color: white !important;
        border: 2px solid #fbbf24 !important;
        font-weight: 700 !important;
    }

    /* Force ALL column layouts to stay side-by-side on mobile */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: auto !important;
        padding: 0 2px !important;
    }
    /* Smaller text for metrics on mobile */
    [data-testid="stMetric"] {
        padding: 8px 4px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 10px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 14px !important;
    }
    /* Specific fix for year/month selector containers */
    .stSelectbox {
        min-width: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Get connection and spreadsheet
        conn = get_gsheets_connection()
        spreadsheet = get_spreadsheet(conn)

        # Get all available months
        from sheets_client import get_all_months
        all_months = get_all_months(spreadsheet)

        # Current month-year
        current_month = datetime.now().strftime("%B_%Y")

        # Month selector
        selected_month = render_month_selector(all_months, current_month)

        # Get or create sheets
        month_sheet = get_or_create_month_sheet(spreadsheet, selected_month)
        config_sheet = get_or_create_config_sheet(spreadsheet)

        # Get config
        config = get_monthly_config(config_sheet, selected_month)

        # Get transactions
        df = get_month_transactions(month_sheet)

        # Calculate KPIs
        kpis = calculate_kpis(df, config["opening_balance"], config["profit_deducted"])

        st.divider()

        # CTA Buttons for quick actions
        st.markdown("##### ⚡ Quick Actions")
        cta_col1, cta_col2 = st.columns(2)
        with cta_col1:
            if st.button("💵 Add Income", use_container_width=True, key="btn_add_income"):
                render_quick_income_form(month_sheet)
        with cta_col2:
            if st.button("💸 Add Expense", use_container_width=True, key="btn_add_expense"):
                render_quick_expense_form(month_sheet)

        st.divider()

        # Render KPIs
        st.subheader("💰 Monthly Summary")
        render_kpi_cards(kpis)

        st.divider()

        # Render chart - full width for mobile
        render_income_expense_chart(kpis)

        st.divider()

        # Render transactions table
        render_transactions_table(df, month_sheet)

        st.divider()

        # Opening Balance - positioned just above Profit Deducted
        st.markdown("##### 🏦 Opening Balance")
        render_opening_balance_section(config_sheet, selected_month)

        st.divider()

        # Profit Deducted - at bottom of page
        st.markdown("##### 💸 Profit Out (Profit Deducted)")
        render_profit_deducted_section(config_sheet, selected_month)

    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")
        st.info("Please check your Google Sheets connection and credentials.")
