import datetime
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
SYMBOL = "GC=F"  # Yahoo Finance ticker for Gold (Use "EURUSD=X" for Euro/USD forex)
LOT_SIZE = 0.01
TIMEFRAME = "15m"
RR_RATIO = 2.0
MAX_TRADES = 1
FALLBACK_SL_PCT = 1.5

def log_msg(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

# --- TECHNICAL INDICATOR FUNCTIONS ---
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

# --- MAIN EXECUTION CYCLE ---
def run_strategy_cycle():
    log_msg(f"STARTING SCAN CYCLE FOR {SYMBOL}")
    
    try:
        # Fetch live/historical candle data via yfinance
        data = yf.download(SYMBOL, period="5d", interval=TIMEFRAME, progress=False)
        if data.empty:
            log_msg("ERROR: No data fetched from Yahoo Finance.")
            return

        # Flatten multi-index columns if present in newer yfinance versions
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        candles = []
        for index, row in data.iterrows():
            candles.append({
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close'])
            })

        if len(candles) < 50:
            log_msg("ERROR: Not enough candles for indicators.")
            return

        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        opens = [c['open'] for c in candles]

        # Calculate ADX & Market Regime
        adx_val = calculate_adx(candles, 14)
        current_price = closes[-1]
        log_msg(f"Current Price: {current_price:.2f} | ADX (14): {adx_val:.1f}")

        # STRATEGY ROUTING
        if adx_val >= 25.0:
            log_msg("Market Regime: TRENDING (ADX >= 25.0)")
            ema50 = calculate_ema(closes, 50)
            c1, c2 = closes[-2], closes[-3]
            e1, e2 = ema50[-2], ema50[-3]
            h2, h3 = highs[-3], highs[-4]
            l2, l3 = lows[-3], lows[-4]

            buy_signal = (c1 > e1 and c2 > e2) and (c1 > h2 and c2 > h3)
            sell_signal = (c1 < e1 and c2 < e2) and (c1 < l2 and c2 < l3)

            if buy_signal:
                log_msg(f"SIGNAL DETECTED: BUY [TREND] on {SYMBOL}")
            elif sell_signal:
                log_msg(f"SIGNAL DETECTED: SELL [TREND] on {SYMBOL}")
            else:
                log_msg("No trend trade setup triggered on this cycle.")

        elif adx_val <= 20.0:
            log_msg("Market Regime: RANGING (ADX <= 20.0)")
            range_high = max(highs[-22:-2])
            range_low = min(lows[-22:-2])
            c1, o1, h1, l1 = closes[-2], opens[-2], highs[-2], lows[-2]

            buy_signal = (l1 <= range_low) and (c1 > o1)
            sell_signal = (h1 >= range_high) and (c1 < o1)

            if buy_signal:
                log_msg(f"SIGNAL DETECTED: BUY [RANGE] on {SYMBOL}")
            elif sell_signal:
                log_msg(f"SIGNAL DETECTED: SELL [RANGE] on {SYMBOL}")
            else:
                log_msg("No range trade setup triggered on this cycle.")
        else:
            log_msg(f"Market Regime: INDECISIVE (ADX: {adx_val:.1f})")

    except Exception as e:
        log_msg(f"EXECUTION ERROR: {str(e)}")

if __name__ == "__main__":
    run_strategy_cycle()
