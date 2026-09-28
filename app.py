import asyncio
import datetime
import threading
import time
import streamlit as st
from metaapi_cloud_sdk import MetaApi

# Mobile Viewport & Cyberpunk Page Setup
st.set_page_config(
    page_title="D-TAY89 FX ENGINE", 
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

# Shared Thread-Safe Logging & State
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False
if "logs" not in st.session_state:
    st.session_state.logs = ["SYSTEM: D-tay89 Multi-Strategy Engine Ready."]
if "account_info" not in st.session_state:
    st.session_state.account_info = {"balance": "--", "equity": "--", "margin": "--", "regime": "STANDBY"}

def add_log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 18:
        st.session_state.logs.pop(0)

# Indicator Calculation Functions
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

# --- BACKGROUND EA SCANNER LOOP ---
def run_ea_background_loop(token, acc_id, symbol, lot_size, timeframe, rr_ratio, max_trades, fallback_sl_pct=1.5):
    """Runs continuously on Render in a dedicated thread independent of the browser UI."""
    async def ea_routine():
        api = MetaApi(token)
        account = await api.metatrader_account_api.get_account(acc_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        last_processed_candle_time = None

        while st.session_state.get("bot_active", False):
            try:
                # 1. Check existing open positions against Max Trades Limit
                positions = await connection.get_positions()
                symbol_positions = [p for p in positions if p['symbol'] == symbol]
                
                if len(symbol_positions) >= max_trades:
                    # Max position limit hit; wait before re-checking
                    await asyncio.sleep(10)
                    continue

                # 2. Fetch recent candles (need 60+ for EMA 50 and ADX 14)
                candles = await connection.get_historical_candles(symbol, timeframe, limit=60)
                if not candles or len(candles) < 50:
                    await asyncio.sleep(10)
                    continue

                # 3. Process execution ONLY on new candle open
                current_candle_time = candles[-1]['time']
                if current_candle_time == last_processed_candle_time:
                    await asyncio.sleep(5)
                    continue

                last_processed_candle_time = current_candle_time

                # Extract OHLC lists
                closes = [c['close'] for c in candles]
                highs = [c['high'] for c in candles]
                lows = [c['low'] for c in candles]
                opens = [c['open'] for c in candles]

                # 4. Detect Market Regime via ADX
                adx_val = calculate_adx(candles, 14)
                
                price = await connection.get_symbol_price(symbol)
                ask, bid = price['ask'], price['bid']

                # 5. STRATEGY ROUTING
                # TREND REGIME (ADX >= 25.0)
                if adx_val >= 25.0:
                    st.session_state.account_info["regime"] = f"TRENDING (ADX: {adx_val:.1f})"
                    ema50 = calculate_ema(closes, 50)
                    
                    c1, c2 = closes[-2], closes[-3]
                    e1, e2 = ema50[-2], ema50[-3]
                    h2, h3 = highs[-3], highs[-4]
                    l2, l3 = lows[-3], lows[-4]

                    # 2-Bar Confirmed Breakout
                    buy_signal = (c1 > e1 and c2 > e2) and (c1 > h2 and c2 > h3)
                    sell_signal = (c1 < e1 and c2 < e2) and (c1 < l2 and c2 < l3)

                    if buy_signal:
                        swing_low = min(lows[-11:-1])
                        sl = swing_low if 0 < swing_low < ask else ask * (1 - (fallback_sl_pct / 100.0))
                        tp = ask + ((ask - sl) * rr_ratio)
                        res = await connection.create_market_buy_order(symbol, lot_size, sl, tp, options={'comment': 'Trend Buy'})
                        add_log(f"EA BUY EXECUTED [TREND]: {lot_size} {symbol} @ {ask} | Ticket: {res.get('orderId')}")

                    elif sell_signal:
                        swing_high = max(highs[-11:-1])
                        sl = swing_high if swing_high > bid else bid * (1 + (fallback_sl_pct / 100.0))
                        tp = bid - ((sl - bid) * rr_ratio)
                        res = await connection.create_market_sell_order(symbol, lot_size, sl, tp, options={'comment': 'Trend Sell'})
                        add_log(f"EA SELL EXECUTED [TREND]: {lot_size} {symbol} @ {bid} | Ticket: {res.get('orderId')}")

                # RANGE REGIME (ADX <= 20.0)
                elif adx_val <= 20.0:
                    st.session_state.account_info["regime"] = f"RANGING (ADX: {adx_val:.1f})"
                    range_high = max(highs[-22:-2])
                    range_low = min(lows[-22:-2])

                    c1, o1, h1, l1 = closes[-2], opens[-2], highs[-2], lows[-2]

                    # Boundary Reversal Pinbar Triggers
                    buy_signal = (l1 <= range_low) and (c1 > o1)
                    sell_signal = (h1 >= range_high) and (c1 < o1)

                    if buy_signal:
                        swing_low = min(lows[-11:-1])
                        sl = swing_low if 0 < swing_low < ask else ask * (1 - (fallback_sl_pct / 100.0))
                        tp = ask + ((ask - sl) * rr_ratio)
                        res = await connection.create_market_buy_order(symbol, lot_size, sl, tp, options={'comment': 'Range Buy'})
                        add_log(f"EA BUY EXECUTED [RANGE]: {lot_size} {symbol} @ {ask} | Ticket: {res.get('orderId')}")

                    elif sell_signal:
                        swing_high = max(highs[-11:-1])
                        sl = swing_high if swing_high > bid else bid * (1 + (fallback_sl_pct / 100.0))
                        tp = bid - ((sl - bid) * rr_ratio)
                        res = await connection.create_market_sell_order(symbol, lot_size, sl, tp, options={'comment': 'Range Sell'})
                        add_log(f"EA SELL EXECUTED [RANGE]: {lot_size} {symbol} @ {bid} | Ticket: {res.get('orderId')}")

                else:
                    st.session_state.account_info["regime"] = f"INDECISIVE (ADX: {adx_val:.1f})"

            except Exception as e:
                add_log(f"EA LOOP ERROR: {str(e)}")
            
            await asyncio.sleep(5)

    asyncio.run(ea_routine())

# --- USER INTERFACE ---
st.markdown("<div class='neon-title'>⚡ D-TAY89 FX ENGINE</div>", unsafe_allow_html=True)
st.markdown("<div class='neon-subtitle'>DYNAMIC MULTI-STRATEGY EA TERMINAL</div>", unsafe_allow_html=True)

# Top Action Bar
col_news, col_stop, col_scan = st.columns(3)
with col_news:
    st.button("📰 NEWS", use_container_width=True)
with col_stop:
    if st.button("⏹ STOP", use_container_width=True):
        st.session_state.bot_active = False
        add_log("ENGINE: Background EA Loop Terminated.")
        st.rerun()
with col_scan:
    if st.button("📈 SCAN", use_container_width=True):
        add_log("SCANNER: Manual sweep triggered.")

st.divider()

# MetaApi Credentials Config
st.subheader("🔑 MetaApi Cloud Connection")
with st.expander("Configure MT4 / MT5 Server Settings", expanded=False):
    api_token = st.text_input("MetaApi Access Token", type="password", key="token_input")
    account_id = st.text_input("MetaApi Account ID", key="acc_input")

async def fetch_account(token, acc_id):
    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(acc_id)
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    return await connection.get_account_information()

if st.button("⚡ CONNECT & SYNC ACCOUNT", use_container_width=True):
    if not api_token or not account_id:
        st.error("Enter MetaApi Access Token & Account ID.")
    else:
        with st.spinner("Connecting to MT5 Cloud..."):
            try:
                data = asyncio.run(fetch_account(api_token, account_id))
                st.session_state.account_info.update({
                    "balance": f"${data.get('balance', 0):,.2f}",
                    "equity": f"${data.get('equity', 0):,.2f}",
                    "margin": f"${data.get('freeMargin', 0):,.2f}"
                })
                add_log(f"CONNECTED: {data.get('server')} | Balance: ${data.get('balance')}")
                st.success("Account Synced!")
            except Exception as e:
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

# Execution & Strategy Parameters (Mobile Responsive 2x2 Grid)
st.subheader("⚙️ Strategy Parameters")
selected_symbol = st.selectbox("Trading Pair", ["XAUUSD", "BTCUSD", "EURUSD", "GBPUSD", "USDJPY"], index=0)

col_left, col_right = st.columns(2)
with col_left:
    lot_size = st.number_input("Lot Size", min_value=0.01, max_value=10.0, value=0.01, step=0.01)
    timeframe = st.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
with col_right:
    rr_ratio = st.number_input("Risk:Reward Ratio", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    max_trades = st.number_input("Max Trades Allowed", min_value=1, max_value=10, value=1, step=1)

st.divider()

# EA Automation Control
st.subheader("🖥 EA Automation Loop")

if not st.session_state.bot_active:
    if st.button("▶ START AUTOMATED EA ENGINE", use_container_width=True):
        if not api_token or not account_id:
            st.error("Please enter MetaApi Token & Account ID above.")
        else:
            st.session_state.bot_active = True
            add_log(f"EA ENGINE STARTED: {selected_symbol} [{timeframe}] | Lot: {lot_size} | Max Trades: {max_trades} | RR: 1:{rr_ratio}")
            
            # Spawn Background Scanner Loop
            t = threading.Thread(
                target=run_ea_background_loop,
                args=(api_token, account_id, selected_symbol, lot_size, timeframe, rr_ratio, max_trades, 1.5),
                daemon=True
            )
            t.start()
            st.rerun()
else:
    st.success(f"⚡ EA ACTIVE: Scanning {selected_symbol} [{timeframe}] (Max Trades: {max_trades})...")

# Live Engine Terminal
terminal_output = "\n".join(st.session_state.logs)
st.code(terminal_output, language="bash")
