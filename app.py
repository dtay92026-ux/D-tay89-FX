import asyncio
import datetime
import threading
import time
import streamlit as st
from tonpo import TonpoClient

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
    st.session_state.logs = ["SYSTEM: D-tay89 Tonpo Engine Ready."]
if "account_info" not in st.session_state:
    st.session_state.account_info = {"balance": "--", "equity": "--", "margin": "--", "regime": "STANDBY"}

def add_log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 18:
        st.session_state.logs.pop(0)

# Technical Indicator Helper Functions
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

# --- BACKGROUND TONPO EA SCANNER LOOP ---
def run_tonpo_ea_background_loop(api_key, acc_id, symbol, lot_size, timeframe, rr_ratio, max_trades, fallback_sl_pct=1.5):
    """24/7 Background scanner loop running on Render via Tonpo API."""
    async def ea_routine():
        while st.session_state.get("bot_active", False):
            try:
                async with TonpoClient.for_user({}, api_key) as client:
                    # 1. Check open positions against Max Trades Limit
                    positions = await client.get_positions(acc_id)
                    symbol_positions = [p for p in positions if p.get('symbol') == symbol]
                    
                    if len(symbol_positions) >= max_trades:
                        await asyncio.sleep(10)
                        continue

                    # 2. Fetch candles
                    candles = await client.get_candles(acc_id, symbol, timeframe, limit=60)
                    if not candles or len(candles) < 50:
                        await asyncio.sleep(10)
                        continue

                    closes = [c['close'] for c in candles]
                    highs = [c['high'] for c in candles]
                    lows = [c['low'] for c in candles]
                    opens = [c['open'] for c in candles]

                    # 3. Detect Market Regime via ADX
                    adx_val = calculate_adx(candles, 14)
                    ticker = await client.get_ticker(acc_id, symbol)
                    ask, bid = ticker.get('ask', closes[-1]), ticker.get('bid', closes[-1])

                    # 4. STRATEGY ROUTING
                    # TREND REGIME (ADX >= 25.0)
                    if adx_val >= 25.0:
                        st.session_state.account_info["regime"] = f"TRENDING (ADX: {adx_val:.1f})"
                        ema50 = calculate_ema(closes, 50)
                        c1, c2 = closes[-2], closes[-3]
                        e1, e2 = ema50[-2], ema50[-3]
                        h2, h3 = highs[-3], highs[-4]
                        l2, l3 = lows[-3], lows[-4]

                        buy_signal = (c1 > e1 and c2 > e2) and (c1 > h2 and c2 > h3)
                        sell_signal = (c1 < e1 and c2 < e2) and (c1 < l2 and c2 < l3)

                        if buy_signal:
                            swing_low = min(lows[-11:-1])
                            sl = swing_low if 0 < swing_low < ask else ask * (1 - (fallback_sl_pct / 100.0))
                            tp = ask + ((ask - sl) * rr_ratio)
                            res = await client.place_market_buy(symbol=symbol, volume=lot_size, sl=sl, tp=tp)
                            add_log(f"TONPO BUY [TREND]: {lot_size} {symbol} @ {ask} | Result: {res}")

                        elif sell_signal:
                            swing_high = max(highs[-11:-1])
                            sl = swing_high if swing_high > bid else bid * (1 + (fallback_sl_pct / 100.0))
                            tp = bid - ((sl - bid) * rr_ratio)
                            res = await client.place_market_sell(symbol=symbol, volume=lot_size, sl=sl, tp=tp)
                            add_log(f"TONPO SELL [TREND]: {lot_size} {symbol} @ {bid} | Result: {res}")

                    # RANGE REGIME (ADX <= 20.0)
                    elif adx_val <= 20.0:
                        st.session_state.account_info["regime"] = f"RANGING (ADX: {adx_val:.1f})"
                        range_high = max(highs[-22:-2])
                        range_low = min(lows[-22:-2])
                        c1, o1, h1, l1 = closes[-2], opens[-2], highs[-2], lows[-2]

                        buy_signal = (l1 <= range_low) and (c1 > o1)
                        sell_signal = (h1 >= range_high) and (c1 < o1)

                        if buy_signal:
                            swing_low = min(lows[-11:-1])
                            sl = swing_low if 0 < swing_low < ask else ask * (1 - (fallback_sl_pct / 100.0))
                            tp = ask + ((ask - sl) * rr_ratio)
                            res = await client.place_market_buy(symbol=symbol, volume=lot_size, sl=sl, tp=tp)
                            add_log(f"TONPO BUY [RANGE]: {lot_size} {symbol} @ {ask} | Result: {res}")

                        elif sell_signal:
                            swing_high = max(highs[-11:-1])
                            sl = swing_high if swing_high > bid else bid * (1 + (fallback_sl_pct / 100.0))
                            tp = bid - ((sl - bid) * rr_ratio)
                            res = await client.place_market_sell(symbol=symbol, volume=lot_size, sl=sl, tp=tp)
                            add_log(f"TONPO SELL [RANGE]: {lot_size} {symbol} @ {bid} | Result: {res}")

                    else:
                        st.session_state.account_info["regime"] = f"INDECISIVE (ADX: {adx_val:.1f})"

            except Exception as e:
                add_log(f"TONPO LOOP ERROR: {str(e)}")
            
            await asyncio.sleep(10)

    asyncio.run(ea_routine())

# --- USER INTERFACE ---
st.markdown("<div class='neon-title'>⚡ D-TAY89 FX ENGINE</div>", unsafe_allow_html=True)
st.markdown("<div class='neon-subtitle'>FREE TONPO CLOUD GATEWAY TERMINAL</div>", unsafe_allow_html=True)

# Top Bar
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

# Tonpo Credentials Config
st.subheader("🔑 Tonpo Cloud Connection")
with st.expander("Configure Free Tonpo Gateway Settings", expanded=False):
    tonpo_api_key = st.text_input("Tonpo API Key", type="password", key="key_input")
    tonpo_acc_id = st.text_input("Tonpo Account ID", key="acc_input")

async def sync_tonpo_account(api_key, acc_id):
    async with TonpoClient.for_user({}, api_key) as client:
        return await client.get_account_info(acc_id)

if st.button("⚡ CONNECT & SYNC ACCOUNT", use_container_width=True):
    if not tonpo_api_key or not tonpo_acc_id:
        st.error("Enter Tonpo API Key & Account ID.")
    else:
        with st.spinner("Syncing via Tonpo Free Gateway..."):
            try:
                info = asyncio.run(sync_tonpo_account(tonpo_api_key, tonpo_acc_id))
                st.session_state.account_info.update({
                    "balance": f"${info.get('balance', 0):,.2f}",
                    "equity": f"${info.get('equity', 0):,.2f}",
                    "margin": f"${info.get('free_margin', 0):,.2f}"
                })
                add_log(f"CONNECTED via Tonpo: Balance ${info.get('balance')}")
                st.success("Account Synced!")
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
        if not tonpo_api_key or not tonpo_acc_id:
            st.error("Please enter Tonpo API Key & Account ID above.")
        else:
            st.session_state.bot_active = True
            add_log(f"EA ENGINE STARTED (TONPO): {selected_symbol} [{timeframe}] | Lot: {lot_size} | Max Trades: {max_trades}")
            
            # Spawn Background Loop
            t = threading.Thread(
                target=run_tonpo_ea_background_loop,
                args=(tonpo_api_key, tonpo_acc_id, selected_symbol, lot_size, timeframe, rr_ratio, max_trades, 1.5),
                daemon=True
            )
            t.start()
            st.rerun()
else:
    st.success(f"⚡ TONPO EA ACTIVE: Monitoring {selected_symbol} [{timeframe}] (Max Trades: {max_trades})...")

# Live Terminal Log
terminal_output = "\n".join(st.session_state.logs)
st.code(terminal_output, language="bash")
