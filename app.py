import datetime
import threading
import requests
import streamlit as st
import pandas as pd
import numpy as np

# Mobile Viewport & Cyberpunk Page Setup
st.set_page_config(
    page_title="D-TAY89 FX ENGINE - OANDA", 
    page_icon="⚡", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Dark Cyber Neon Styling
st.markdown("""
    <style>
    .stApp { background-color: #08090d; color: #e0e6ed; }
    .neon-title {
        text-align: center; font-weight: 900; font-size: 26px; color: #00f3ff;
        text-shadow: 0 0 15px rgba(0, 243, 255, 0.7); margin-bottom: 2px;
    }
    .neon-subtitle {
        text-align: center; color: #ff0055; font-size: 11px;
        letter-spacing: 2px; font-weight: bold; text-transform: uppercase; margin-bottom: 15px;
    }
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] {
        background-color: #121520 !important; color: #00f3ff !important;
        border: 1px solid #1a2236 !important; border-radius: 8px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #00ff88 !important; font-weight: 800; font-size: 19px !important;
    }
    div.stButton > button {
        width: 100% !important; border-radius: 8px !important; font-weight: 800 !important;
        font-size: 14px !important; height: 3.2em !important; background-color: #121624 !important;
        color: #00f3ff !important; border: 1px solid #00f3ff !important;
    }
    div.stButton > button:hover { background-color: #00f3ff !important; color: #08090d !important; }
    </style>
""", unsafe_allow_html=True)

# Shared Thread-Safe State
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False
if "logs" not in st.session_state:
    st.session_state.logs = ["SYSTEM: D-tay89 OANDA Native REST Engine Ready."]
if "account_info" not in st.session_state:
    st.session_state.account_info = {"balance": "--", "equity": "--", "margin": "--", "regime": "STANDBY"}

def add_log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 18:
        st.session_state.logs.pop(0)

# Technical Indicators
def calculate_ema(closes, period=50):
    k = 2 / (period + 1)
    ema = [closes[0]]
    for price in closes[1:]:
        ema.append((price * k) + (ema[-1] * (1 - k)))
    return ema

def calculate_adx(candles, period=14):
    if len(candles) < period * 2:
        return 0.0
    tr_list, pdm_list, mdm_list = [], [], []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]['high'], candles[i]['low'], candles[i-1]['close']
        ph, pl = candles[i-1]['high'], candles[i-1]['low']
        
        tr = max(h - l, abs(h - pc), abs(l - pc))
        pdm = (h - ph) if (h - ph) > (pl - l) and (h - ph) > 0 else 0
        mdm = (pl - l) if (pl - l) > (h - ph) and (pl - l) > 0 else 0
        
        tr_list.append(tr)
        pdm_list.append(pdm)
        mdm_list.append(mdm)

    smooth_tr = sum(tr_list[:period])
    smooth_pdm = sum(pdm_list[:period])
    smooth_mdm = sum(mdm_list[:period])

    dx_list = []
    for i in range(period, len(tr_list)):
        smooth_tr = smooth_tr - (smooth_tr / period) + tr_list[i]
        smooth_pdm = smooth_pdm - (smooth_pdm / period) + pdm_list[i]
        smooth_mdm = smooth_mdm - (smooth_mdm / period) + mdm_list[i]

        pdi = 100 * (smooth_pdm / smooth_tr) if smooth_tr > 0 else 0
        mdi = 100 * (smooth_mdm / smooth_tr) if smooth_tr > 0 else 0
        di_diff = abs(pdi - mdi)
        di_sum = pdi + mdi
        dx = 100 * (di_diff / di_sum) if di_sum > 0 else 0
        dx_list.append(dx)

    return sum(dx_list[-period:]) / period if len(dx_list) >= period else 0.0

# --- OANDA API HELPER FUNCTIONS ---
def get_base_url(env_type):
    if env_type == "Practice (Demo)":
        return "https://api-fxpractice.oanda.com"
    return "https://api-fxtrade.oanda.com"

def fetch_oanda_account(token, account_id, env_type):
    base_url = get_base_url(env_type)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{base_url}/v3/accounts/{account_id}/summary"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("account", {})
    else:
        raise Exception(f"API Error {resp.status_code}: {resp.text}")

def fetch_oanda_candles(token, account_id, env_type, instrument, granularity="M15", count=60):
    base_url = get_base_url(env_type)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{base_url}/v3/instruments/{instrument}/candles?granularity={granularity}&count={count}&price=M"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json().get("candles", [])
        formatted = []
        for c in data:
            if c.get("complete", True):
                mid = c.get("mid", {})
                formatted.append({
                    'open': float(mid.get('o', 0)),
                    'high': float(mid.get('h', 0)),
                    'low': float(mid.get('l', 0)),
                    'close': float(mid.get('c', 0))
                })
        return formatted
    return []

def place_oanda_order(token, account_id, env_type, instrument, units, stop_loss=None, take_profit=None):
    base_url = get_base_url(env_type)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{base_url}/v3/accounts/{account_id}/orders"
    
    order_data = {
        "order": {
            "units": str(units),
            "instrument": instrument,
            "timeInForce": "FOK",
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }
    if stop_loss:
        order_data["order"]["stopLossOnFill"] = {"price": f"{stop_loss:.5f}"}
    if take_profit:
        order_data["order"]["takeProfitOnFill"] = {"price": f"{take_profit:.5f}"}

    resp = requests.post(url, headers=headers, json=order_data, timeout=10)
    return resp.json()

# --- BACKGROUND OANDA LOOP ---
def run_oanda_ea_loop(api_token, acc_id, env_type, symbol, units, timeframe, rr_ratio, max_trades):
    granularity_map = {"5m": "M5", "15m": "M15", "1h": "H1", "4h": "H4"}
    gran = granularity_map.get(timeframe, "M15")

    while st.session_state.get("bot_active", False):
        try:
            base_url = get_base_url(env_type)
            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
            trades_resp = requests.get(f"{base_url}/v3/accounts/{acc_id}/openTrades", headers=headers, timeout=10)
            if trades_resp.status_code == 200:
                open_trades = trades_resp.json().get("trades", [])
                symbol_trades = [t for t in open_trades if t.get('instrument') == symbol]
                if len(symbol_trades) >= max_trades:
                    import time
                    time.sleep(10)
                    continue

            candles = fetch_oanda_candles(api_token, acc_id, env_type, symbol, granularity=gran, count=60)
            if not candles or len(candles) < 50:
                import time
                time.sleep(10)
                continue

            closes = [c['close'] for c in candles]
            highs = [c['high'] for c in candles]
            lows = [c['low'] for c in candles]
            opens = [c['open'] for c in candles]

            adx_val = calculate_adx(candles, 14)
            current_price = closes[-1]

            if adx_val >= 25.0:
                st.session_state.account_info["regime"] = f"TRENDING (ADX: {adx_val:.1f})"
                ema50 = calculate_ema(closes, 50)
                c1, c2 = closes[-2], closes[-3]
                e1, e2 = ema50[-2], ema50[-3]
                h2, h3 = highs[-3], highs[-4]
                l2, l3 = lows[-3], lows[-4]

                if (c1 > e1 and c2 > e2) and (c1 > h2 and c2 > h3):
                    sl = current_price * 0.985
                    tp = current_price + ((current_price - sl) * rr_ratio)
                    res = place_oanda_order(api_token, acc_id, env_type, symbol, units, sl, tp)
                    add_log(f"OANDA BUY [TREND]: {units} {symbol} | Executed")
                elif (c1 < e1 and c2 < e2) and (c1 < l2 and c2 < l3):
                    sl = current_price * 1.015
                    tp = current_price - ((sl - current_price) * rr_ratio)
                    res = place_oanda_order(api_token, acc_id, env_type, symbol, -units, sl, tp)
                    add_log(f"OANDA SELL [TREND]: {units} {symbol} | Executed")

            elif adx_val <= 20.0:
                st.session_state.account_info["regime"] = f"RANGING (ADX: {adx_val:.1f})"
                range_high = max(highs[-22:-2])
                range_low = min(lows[-22:-2])
                c1, o1, h1, l1 = closes[-2], opens[-2], highs[-2], lows[-2]

                if (l1 <= range_low) and (c1 > o1):
                    sl = current_price * 0.985
                    tp = current_price + ((current_price - sl) * rr_ratio)
                    res = place_oanda_order(api_token, acc_id, env_type, symbol, units, sl, tp)
                    add_log(f"OANDA BUY [RANGE]: {units} {symbol} | Executed")
                elif (h1 >= range_high) and (c1 < o1):
                    sl = current_price * 1.015
                    tp = current_price - ((sl - current_price) * rr_ratio)
                    res = place_oanda_order(api_token, acc_id, env_type, symbol, -units, sl, tp)
                    add_log(f"OANDA SELL [RANGE]: {units} {symbol} | Executed")
            else:
                st.session_state.account_info["regime"] = f"INDECISIVE (ADX: {adx_val:.1f})"

        except Exception as e:
            add_log(f"LOOP ERROR: {str(e)}")
        
        import time
        time.sleep(10)

# --- USER INTERFACE ---
st.markdown("<div class='neon-title'>⚡ D-TAY89 FX ENGINE</div>", unsafe_allow_html=True)
st.markdown("<div class='neon-subtitle'>OANDA NATIVE REST API TERMINAL</div>", unsafe_allow_html=True)

col_news, col_stop, col_scan = st.columns(3)
with col_news:
    st.button("📰 NEWS", use_container_width=True)
with col_stop:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.bot_active = False
        add_log("ENGINE: Background Loop Terminated.")
        st.rerun()
with col_scan:
    if st.button("📈 SCAN", use_container_width=True):
        add_log("SCANNER: Manual sweep triggered.")

st.divider()

# OANDA Credentials Config
st.subheader("🔑 OANDA API Connection")
with st.expander("Configure API & Account Settings", expanded=True):
    env_type = st.selectbox("Environment", ["Practice (Demo)", "Live (Real Account)"], index=0)
    api_token = st.text_input("OANDA Access Token", type="password", key="token_input")
    acc_id = st.text_input("OANDA Account ID", key="acc_input")

if st.button("⚡ CONNECT & SYNC ACCOUNT", use_container_width=True):
    if not api_token or not acc_id:
        st.error("Enter OANDA Token & Account ID.")
    else:
        with st.spinner("Connecting to OANDA REST API..."):
            try:
                acc = fetch_oanda_account(api_token, acc_id, env_type)
                st.session_state.account_info.update({
                    "balance": f"${float(acc.get('balance', 0)):,.2f}",
                    "equity": f"${float(acc.get('NAV', 0)):,.2f}",
                    "margin": f"${float(acc.get('marginAvailable', 0)):,.2f}"
                })
                add_log(f"CONNECTED: Balance ${float(acc.get('balance', 0)):,.2f}")
                st.success("Account Synced Successfully!")
            except Exception as e:
                add_log(f"SYNC ERROR: {str(e)}")
                st.error(f"Sync Error: {str(e)}")

st.divider()

# Live Broker Stats Metrics
st.subheader("📊 Live Broker Stats")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="BALANCE", value=st.session_state.account_info["balance"])
with m2:
    st.metric(label="EQUITY", value=st.session_state.account_info["equity"])
with m3:
    st.metric(label="REGIME", value=st.session_state.account_info["regime"])

st.divider()

# Strategy Parameters
st.subheader("⚙️ Strategy Parameters")
selected_symbol = st.selectbox("Trading Pair", ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY"], index=0)

col_left, col_right = st.columns(2)
with col_left:
    units = st.number_input("Units / Lot Size", min_value=1, max_value=100000, value=100, step=1)
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
with col_right:
    rr_ratio = st.number_input("Risk:Reward Ratio", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    max_trades = st.number_input("Max Trades Allowed", min_value=1, max_value=10, value=1, step=1)

st.divider()

# Automation Control
st.subheader("🖥 API Automation Loop")

if not st.session_state.bot_active:
    if st.button("▶ START AUTOMATED API ENGINE", use_container_width=True):
        if not api_token or not acc_id:
            st.error("Please enter OANDA Token & Account ID above.")
        else:
            st.session_state.bot_active = True
            add_log(f"API ENGINE STARTED: {selected_symbol} [{timeframe}] | Units: {units}")
            
            t = threading.Thread(
                target=run_oanda_ea_loop,
                args=(api_token, acc_id, env_type, selected_symbol, units, timeframe, rr_ratio, max_trades),
                daemon=True
            )
            t.start()
            st.rerun()
else:
    st.success(f"⚡ API ENGINE ACTIVE: Monitoring {selected_symbol} [{timeframe}]...")

# Live Terminal Log
terminal_output = "\n".join(st.session_state.logs)
st.code(terminal_output, language="bash")
