"""Server-side password gate for the private research page."""
from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 390_000


def generate_hash(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(24)
    encoded = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return salt.hex(), encoded.hex()


def verify(password: str, salt_hex: str, expected_hex: str) -> bool:
    try:
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(expected_hex)
        if len(salt) < 16 or len(expected) != 32 or not password:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def render_gate(st) -> None:
    """Stop this Streamlit run before a private loader is created or called."""
    if st.session_state.get("trust_authorized") is True:
        st.markdown("<style>.st-key-trust_logout button {color:#fff !important}</style>", unsafe_allow_html=True)
        if st.sidebar.button("退出信托研究", key="trust_logout"):
            for key in tuple(st.session_state):
                if key.startswith("trust_"):
                    del st.session_state[key]
            st.rerun()
        return
    try:
        salt = st.secrets.get("TRUST_PASSWORD_SALT", "")
        expected = st.secrets.get("TRUST_PASSWORD_HASH", "")
    except FileNotFoundError:
        salt = expected = ""
    st.markdown("## 股东与信托研究")
    if not salt or not expected:
        st.info("研究模块尚未配置访问密码。")
        st.stop()
    with st.form("trust_login", clear_on_submit=True):
        candidate = st.text_input("访问密码", type="password", autocomplete="off")
        submitted = st.form_submit_button("进入研究")
    if submitted:
        if verify(candidate, salt, expected):
            st.session_state["trust_authorized"] = True
            st.rerun()
        else:
            st.error("密码不正确。")
    st.stop()
