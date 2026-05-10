"""Authentication module for rental dashboard."""
import streamlit as st

MAX_LOGIN_ATTEMPTS = 3


def init_auth_state():
    """Initialize authentication state in session."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "locked" not in st.session_state:
        st.session_state.locked = False


def login(password_input: str) -> bool:
    """
    Attempt login with provided password.

    Args:
        password_input: Password entered by user

    Returns:
        True if login successful, False otherwise
    """
    init_auth_state()

    if st.session_state.locked:
        return False

    correct_password = st.secrets.get("APP_PASSWORD", "")

    if password_input == correct_password:
        st.session_state.authenticated = True
        st.session_state.login_attempts = 0
        return True
    else:
        st.session_state.login_attempts += 1
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.locked = True
        return False


def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.login_attempts = 0
    st.session_state.locked = False


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    init_auth_state()
    return st.session_state.authenticated


def is_locked() -> bool:
    """Check if system is locked due to failed attempts."""
    init_auth_state()
    return st.session_state.locked


def get_remaining_attempts() -> int:
    """Get number of remaining login attempts."""
    init_auth_state()
    return max(0, MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts)


def render_login_page():
    """Render the login page - mobile first."""
    # Centered layout for mobile
    col1, col2, col3 = st.columns([1, 6, 1])

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>🏠</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>PG Expense Manager</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Rental Property Tracker</p>", unsafe_allow_html=True)
        st.markdown("---")

        if is_locked():
            st.error("🔒 **Locked**: Too many failed attempts. Refresh to retry.")
            return

        with st.form("login_form"):
            st.markdown("<h4 style='text-align: center;'>Login</h4>", unsafe_allow_html=True)

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
                label_visibility="collapsed"
            )

            submitted = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)

            if submitted:
                if login(password):
                    st.success("✅ Welcome!")
                    st.rerun()
                else:
                    remaining = get_remaining_attempts()
                    if is_locked():
                        st.error("🔒 Locked! Refresh page.")
                    else:
                        st.error(f"❌ Wrong password. {remaining} tries left.")
