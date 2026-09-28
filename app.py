import streamlit as st

# Mobile page setup
st.set_page_config(
    page_title="D-tay89 FX Engine", 
    page_icon="⚡", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Custom Styling (Dark Neon Theme)
st.markdown("""
    <style>
    .stApp { background-color: #0b0c10; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    div[data-testid="stMetricValue"] { color: #ff3333; }
    </style>
""", unsafe_allow_html=True)

# Main Title
st.markdown("<h1 style='text-align: center; color: #ff3333;'>⚡ D-tay89 FX Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Execution & Account Control Center</p>", unsafe_allow_html=True)

st.divider()

# Session State Initializers
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False

# Quick Action Buttons in Horizontal Columns
col_news, col_stop, col_scan = st.columns(3)
with col_news:
    st.button("📰 NEWS")
with col_stop:
    if st.button("⏹ STOP"):
        st.session_state.bot_active = False
        st.rerun()
with col_scan:
    st.button("📈 SCAN")

st.divider()

# Engine Status Cards
st.subheader("Engine Status")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(label="SYMBOL", value=st.session_state.get("selected_symbol", "XAUUSD"))
with c2:
    st.metric(label="STATUS", value="ACTIVE" if st.session_state.bot_active else "OFFLINE")
with c3:
    st.metric(label="LOT SIZE", value=str(st.session_state.get("selected_lot", 0.01)))

st.divider()

# Account Connection Details
st.subheader("🔑 Account Credentials")
with st.expander("Broker Connection Settings", expanded=False):
    account_id = st.text_input("MetaTrader Account ID", value="", placeholder="e.g. 12345678")
    server_name = st.text_input("Broker Server", value="", placeholder="e.g. Exness-Real11")
    meta_api_token = st.text_input("MetaApi Token", type="password", placeholder="Enter MetaApi Cloud Token")

st.divider()

# Execution Controls (Pair & Lot Selection)
st.subheader("⚡ Trade Parameters")

selected_symbol = st.selectbox(
    "Trading Pair",
    ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD"],
    index=0
)
st.session_state.selected_symbol = selected_symbol

col_lot, col_sl, col_tp = st.columns(3)
with col_lot:
    lot_size = st.number_input("Lot Size", min_value=0.01, max_value=10.0, value=0.01, step=0.01)
    st.session_state.selected_lot = lot_size
with col_sl:
    stop_loss_pips = st.number_input("SL (Pips)", min_value=0, value=30)
with col_tp:
    take_profit_pips = st.number_input("TP (Pips)", min_value=0, value=60)

# Instant Execution Buttons
col_buy, col_sell = st.columns(2)

with col_buy:
    if st.button("🟢 BUY NOW"):
        if st.session_state.bot_active:
            st.success(f"BUY order sent for {lot_size} lots on {selected_symbol}!")
            # Trigger execution function here
        else:
            st.error("Enable Engine below before executing trades.")

with col_sell:
    if st.button("🔴 SELL NOW"):
        if st.session_state.bot_active:
            st.warning(f"SELL order sent for {lot_size} lots on {selected_symbol}!")
            # Trigger execution function here
        else:
            st.error("Enable Engine below before executing trades.")

st.divider()

# Engine Activation Switch
if not st.session_state.bot_active:
    if st.button("▶ START AUTOMATED ENGINE"):
        st.session_state.bot_active = True
        st.rerun()
else:
    st.success(f"D-tay89 Engine ACTIVE — Monitoring {selected_symbol} @ {lot_size} Lots")
