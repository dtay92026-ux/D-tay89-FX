import streamlit as st

# Mobile viewport and page setup
st.set_page_config(
    page_title="D-tay89 FX Engine", 
    page_icon="⚡", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Custom dark theme CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0c10;
        color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        background-color: #ff3333;
        color: #ffffff;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        height: 3em;
    }
    </style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ D-tay89 FX Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Automated Execution Dashboard</p>", unsafe_allow_html=True)

st.divider()

# Session State
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False

# Action Buttons
col1, col2, col3 = st.columns(3)
with col1:
    st.button("📰 NEWS")
with col2:
    if st.button("⏹ STOP"):
        st.session_state.bot_active = False
with col3:
    st.button("📈 SCAN")

st.divider()

# Status Cards
st.subheader("Engine Status")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(label="SYMBOLS", value="1")
with c2:
    st.metric(label="STATUS", value="ACTIVE" if st.session_state.bot_active else "OFFLINE")
with c3:
    st.metric(label="RUNNING", value="1" if st.session_state.bot_active else "0")

st.divider()

# Controls
license_key = st.text_input("License Key", value="DTAY-89-PRO", type="password")

if license_key:
    if not st.session_state.bot_active:
        if st.button("▶ START ENGINE"):
            st.session_state.bot_active = True
            st.rerun()
    else:
        st.success("D-tay89 Engine is actively scanning market feeds.")

st.divider()
st.subheader("Chart Scanner")
if st.session_state.bot_active:
    st.warning("⚡ Scanner Active: Monitoring EUR/USD & XAU/USD")
else:
    st.info("Scanner standby. Tap 'START ENGINE' to commence scanning.")
