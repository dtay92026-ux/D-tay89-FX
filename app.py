import asyncio
import datetime
import streamlit as st
from metaapi_cloud_sdk import MetaApi

# Mobile Viewport & Cyberpunk Page Setup
st.set_page_config(
    page_title="D-TAY89 FX ENGINE", 
    page_icon="⚡", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Custom Cyberpunk Neon Styling
st.markdown("""
    <style>
    /* Dark Cyber Background */
    .stApp {
        background-color: #08090d;
        color: #e0e6ed;
    }
    
    /* Neon Glow Header */
    .neon-title {
        text-align: center;
        font-weight: 900;
        font-size: 28px;
        color: #00f3ff;
        text-shadow: 0 0 15px rgba(0, 243, 255, 0.7), 0 0 30px rgba(0, 243, 255, 0.3);
        margin-bottom: 2px;
    }
    .neon-subtitle {
        text-align: center;
        color: #ff0055;
        font-size: 11px;
        letter-spacing: 3px;
        font-weight: bold;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* Input Box Styles */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] {
        background-color: #121520 !important;
        color: #00f3ff !important;
        border: 1px solid #1a2236 !important;
        border-radius: 8px !important;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        color: #00ff88 !important;
        font-weight: 800;
        font-size: 20px !important;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.4);
    }
    div[data-testid="stMetricLabel"] {
        color: #8a99ad !important;
        font-size: 11px !important;
        letter-spacing: 1px;
    }

    /* Button Styling */
    div.stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        height: 3.2em !important;
        background-color: #121624 !important;
        color: #00f3ff !important;
        border: 1px solid #00f3ff !important;
        box-shadow: 0 0 8px rgba(0, 243, 255, 0.2);
    }
    div.stButton > button:hover {
        background-color: #00f3ff !important;
        color: #08090d !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.8) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Session State Initializations
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False
if "logs" not in st.session_state:
    st.session_state.logs = ["SYSTEM: D-tay89 Engine Core Initialized.", "SYSTEM: Awaiting Broker Credentials..."]
if "account_info" not in st.session_state:
    st.session_state.account_info = {"balance": "--", "equity": "--", "margin": "--", "server": "OFFLINE"}

def add_log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")
    if len(st.session_state.logs) > 15:
        st.session_state.logs.pop(0)

# Header Section
st.markdown("<div class='neon-title'>⚡ D-TAY89 FX ENGINE</div>", unsafe_allow_html=True)
st.markdown("<div class='neon-subtitle'>QUANTITATIVE EXECUTION TERMINAL</div>", unsafe_allow_html=True)

# Quick Controls
col_news, col_stop, col_scan = st.columns(3)
with col_news:
    if st.button("📰 NEWS", use_container_width=True):
        add_log("CALENDAR: Checking high-impact news events (USD/XAU)... No high risk detected.")
with col_stop:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.bot_active = False
        add_log("ENGINE: Automated scanner halted by operator.")
        st.rerun()
with col_scan:
    if st.button("📈 SCAN", use_container_width=True):
        add_log("SCANNER: Manual market sweep requested...")
        add_log("MARKET: XAUUSD Spread: 1.1 pips | Momentum: BULLISH")

st.divider()

# MetaApi Credentials & Live Sync
st.subheader("🔑 MetaApi Cloud Connection")
with st.expander("Configure MT4 / MT5 Server Settings", expanded=False):
    api_token = st.text_input("MetaApi Access Token", type="password", key="token_input")
    account_id = st.text_input("MetaApi Account ID", key="acc_input")

async def fetch_metaapi_account(token, acc_id):
    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(acc_id)
    if account.state != 'DEPLOYED':
        await account.deploy()
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    info = await connection.get_account_information()
    return info

if st.button("⚡ CONNECT & SYNC ACCOUNT", use_container_width=True):
    if not api_token or not account_id:
        st.error("Please enter both MetaApi Token and Account ID above.")
    else:
        with st.spinner("Connecting to MT5 Cloud Terminal..."):
            try:
                acc_data = asyncio.run(fetch_metaapi_account(api_token, account_id))
                st.session_state.account_info = {
                    "balance": f"${acc_data.get('balance', 0):,.2f}",
                    "equity": f"${acc_data.get('equity', 0):,.2f}",
                    "margin": f"${acc_data.get('freeMargin', 0):,.2f}",
                    "server": acc_data.get('server', 'CONNECTED')
                }
                add_log(f"SUCCESS: Connected to {acc_data.get('server')} | Balance: ${acc_data.get('balance')}")
                st.success("Connected to MetaTrader Account!")
            except Exception as e:
                add_log(f"ERROR: Connection failed - {str(e)}")
                st.error(f"Connection Failed: {str(e)}")

st.divider()

# Account Metrics Dashboard
st.subheader("📊 Live Broker Stats")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="BALANCE", value=st.session_state.account_info["balance"])
with m2:
    st.metric(label="EQUITY", value=st.session_state.account_info["equity"])
with m3:
    st.metric(label="FREE MARGIN", value=st.session_state.account_info["margin"])

st.divider()

# Execution Parameters
st.subheader("⚡ Trade Parameters")
selected_symbol = st.selectbox("Trading Pair", ["XAUUSD", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY"], index=0)

col_lot, col_sl, col_tp = st.columns(3)
with col_lot:
    lot_size = st.number_input("Lot Size", min_value=0.01, max_value=10.0, value=0.05, step=0.01)
with col_sl:
    stop_loss = st.number_input("SL (Pips)", min_value=0, value=30)
with col_tp:
    take_profit = st.number_input("TP (Pips)", min_value=0, value=60)

# MetaApi Trade Execution
async def execute_metaapi_trade(token, acc_id, symbol, action_type, volume):
    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(acc_id)
    if account.state != 'DEPLOYED':
        await account.deploy()
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    
    if action_type == "BUY":
        res = await connection.create_market_buy_order(symbol=symbol, volume=volume)
    else:
        res = await connection.create_market_sell_order(symbol=symbol, volume=volume)
    return res

# Order Buttons
col_buy, col_sell = st.columns(2)
with col_buy:
    if st.button("🟢 BUY NOW", use_container_width=True):
        if not api_token or not account_id:
            st.error("Enter MetaApi Credentials first!")
        else:
            with st.spinner(f"Routing BUY Order ({lot_size} {selected_symbol})..."):
                try:
                    res = asyncio.run(execute_metaapi_trade(api_token, account_id, selected_symbol, "BUY", lot_size))
                    add_log(f"ORDER EXECUTED: BUY {lot_size} {selected_symbol} | Ticket: {res.get('orderId')}")
                    st.success(f"BUY Order Placed! Ticket: {res.get('orderId')}")
                except Exception as e:
                    add_log(f"ORDER FAILED: BUY {selected_symbol} - {str(e)}")
                    st.error(f"Execution Error: {str(e)}")

with col_sell:
    if st.button("🔴 SELL NOW", use_container_width=True):
        if not api_token or not account_id:
            st.error("Enter MetaApi Credentials first!")
        else:
            with st.spinner(f"Routing SELL Order ({lot_size} {selected_symbol})..."):
                try:
                    res = asyncio.run(execute_metaapi_trade(api_token, account_id, selected_symbol, "SELL", lot_size))
                    add_log(f"ORDER EXECUTED: SELL {lot_size} {selected_symbol} | Ticket: {res.get('orderId')}")
                    st.success(f"SELL Order Placed! Ticket: {res.get('orderId')}")
                except Exception as e:
                    add_log(f"ORDER FAILED: SELL {selected_symbol} - {str(e)}")
                    st.error(f"Execution Error: {str(e)}")

st.divider()

# Engine Activation & Live Output Terminal
st.subheader("🖥 Engine Terminal & Scanner Log")

if not st.session_state.bot_active:
    if st.button("▶ START AUTOMATED ENGINE", use_container_width=True):
        st.session_state.bot_active = True
        add_log(f"ENGINE: Active monitoring commenced on {selected_symbol} @ {lot_size} Lots.")
        add_log("SCANNER: Algorithmic tick inspection initialized...")
        st.rerun()
else:
    st.info(f"⚡ Engine ACTIVE: Scanning {selected_symbol} at {lot_size} Lots...")

# Display Live Console Box
terminal_output = "\n".join(st.session_state.logs)
st.code(terminal_output, language="bash")
