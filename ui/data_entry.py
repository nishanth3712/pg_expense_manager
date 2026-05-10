"""Data entry UI component for rental dashboard."""
import streamlit as st
from datetime import datetime

from sheets_client import (
    get_gsheets_connection, get_spreadsheet, get_or_create_month_sheet,
    add_transaction, EXPENSE_CATEGORIES
)


def render_income_entry(month_sheet):
    """Render income/rent entry form - mobile first."""
    st.subheader("💵 Add Rent/Income")

    with st.form("income_form"):
        # Stack vertically for mobile
        income_date = st.date_input(
            "Date",
            value=datetime.now(),
            format="DD/MM/YYYY"
        )

        c1, c2 = st.columns(2)
        with c1:
            income_mode = st.selectbox(
                "Mode",
                options=["Cash", "Bank"],
                index=1
            )
        with c2:
            income_amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=1000.0,
                format="%.2f"
            )

        income_description = st.text_input(
            "Description",
            value="Monthly Rent",
            placeholder="e.g., Tenant Name"
        )

        submitted = st.form_submit_button("➕ Add Income", type="primary", use_container_width=True)

        if submitted:
            if income_amount <= 0:
                st.error("❌ Amount must be greater than 0")
                return

            try:
                date_str = income_date.strftime("%d/%m/%Y")
                add_transaction(
                    worksheet=month_sheet,
                    date=date_str,
                    category="Rent",
                    description=income_description,
                    txn_type="Income",
                    mode=income_mode,
                    amount=income_amount
                )
                st.success("✅ Income added!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def render_expense_entry(month_sheet):
    """Render expense entry form - mobile first."""
    st.subheader("💸 Add Expense")

    with st.form("expense_form"):
        # Stack vertically for mobile
        expense_date = st.date_input(
            "Date",
            value=datetime.now(),
            key="expense_date",
            format="DD/MM/YYYY"
        )

        c1, c2 = st.columns(2)
        with c1:
            expense_category = st.selectbox(
                "Category",
                options=EXPENSE_CATEGORIES,
                index=0
            )
        with c2:
            expense_mode = st.selectbox(
                "Payment Mode",
                options=["Cash", "Bank"],
                key="expense_mode",
                index=1
            )

        c3, c4 = st.columns(2)
        with c3:
            expense_amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                key="expense_amount",
                step=100.0,
                format="%.2f"
            )

        expense_description = st.text_input(
            "Description",
            placeholder="e.g., Plumbing repair, Electric bill"
        )

        submitted = st.form_submit_button("➕ Add Expense", type="primary", use_container_width=True)

        if submitted:
            if expense_amount <= 0:
                st.error("❌ Amount must be greater than 0")
                return

            if not expense_description.strip():
                st.error("❌ Please provide a description")
                return

            try:
                date_str = expense_date.strftime("%d/%m/%Y")
                add_transaction(
                    worksheet=month_sheet,
                    date=date_str,
                    category=expense_category,
                    description=expense_description,
                    txn_type="Expense",
                    mode=expense_mode,
                    amount=expense_amount
                )
                st.success("✅ Expense added!")
                st.snow()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def render_data_entry():
    """Main data entry rendering function."""
    st.title("📝 Data Entry")

    try:
        # Get connection and spreadsheet
        conn = get_gsheets_connection()
        spreadsheet = get_spreadsheet(conn)

        # Get current month
        current_month = datetime.now().strftime("%B_%Y")

        # Allow selecting a different month for data entry
        from sheets_client import get_all_months
        all_months = get_all_months(spreadsheet)
        month_options = all_months if all_months else [current_month]

        selected_month = st.selectbox(
            "📅 Select Month for Data Entry",
            options=month_options,
            index=month_options.index(current_month) if current_month in month_options else 0
        )

        # Get or create the month sheet
        month_sheet = get_or_create_month_sheet(spreadsheet, selected_month)

        st.info(f"Adding entries to: **{selected_month}**")
        st.divider()

        # Render forms
        render_income_entry(month_sheet)

        st.divider()

        render_expense_entry(month_sheet)

    except Exception as e:
        st.error(f"❌ Error loading data entry: {str(e)}")
        st.info("Please check your Google Sheets connection and credentials.")
