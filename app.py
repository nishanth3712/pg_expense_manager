"""
PG Expense Manager - Streamlit Rental Financial Dashboard

A comprehensive dashboard for tracking rental property finances using Google Sheets.
"""
import streamlit as st

from auth import is_authenticated, render_login_page, logout
from ui import render_dashboard, render_data_entry, render_yearly_overview

# Page configuration - Mobile first
st.set_page_config(
    page_title="PG Expense Manager",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "PG Expense Manager - Track your rental property finances"
    }
)

# Mobile-first custom CSS
st.markdown("""
<style>
    /* Mobile-first base styles */
    .stApp {
        max-width: 100% !important;
    }

    /* Touch-friendly buttons */
    .stButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
    }

    /* Form inputs for mobile */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        min-height: 48px !important;
        font-size: 16px !important;
    }

    /* Date picker for mobile */
    .stDateInput > div > div > input {
        min-height: 48px !important;
        font-size: 16px !important;
    }

    /* Hide default streamlit elements on mobile */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hide number input spinners globally */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none !important;
        margin: 0 !important;
    }
    input[type="number"] {
        -moz-appearance: textfield !important;
    }

    /* Better spacing for mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Card-like containers */
    div.stMarkdown h1 {
        font-size: 24px !important;
    }

    div.stMarkdown h2 {
        font-size: 20px !important;
    }

    div.stMarkdown h3 {
        font-size: 18px !important;
    }

    /* Bottom navigation for mobile */
    .mobile-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px;
        border-top: 1px solid #ddd;
        display: flex;
        justify-content: space-around;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Overview"
    if "show_income_form" not in st.session_state:
        st.session_state.show_income_form = False
    if "show_expense_form" not in st.session_state:
        st.session_state.show_expense_form = False


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/property.png", width=80)
        st.title("PG Expense Manager")
        st.markdown("---")

        # Navigation
        st.subheader("📍 Navigation")

        pages = ["Overview", "Yearly View"]

        for page in pages:
            if st.button(
                f"{'📊' if page == 'Overview' else '📅'} {page}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page else "secondary"
            ):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")

        # User info and logout
        st.subheader("👤 User")
        st.success("✅ Logged In")

        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
            st.rerun()



def render_footer():
    """Render the footer."""
    st.markdown("---")
    st.caption("🏠 PG Expense Manager | Built with Streamlit | © 2024")


def main():
    """Main application entry point."""
    init_session_state()

    # Check authentication
    if not is_authenticated():
        render_login_page()
        return

    # Render sidebar
    render_sidebar()

    # Render main content based on selected page
    page = st.session_state.current_page

    if page == "Overview":
        render_dashboard()
    elif page == "Yearly View":
        render_yearly_overview()

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
