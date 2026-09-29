import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time

# ==========================================
# UNIVERSAL BROKER CONFIGURATION
# Change these details for whichever broker you want to use
# ==========================================
ACCOUNT_LOGIN = 12345678          # Your Account Number (Login ID)
ACCOUNT_PASSWORD = "YourPassword" # Your Trading Account Password
ACCOUNT_SERVER = "Broker-Server"  # Exact Server Name provided by your broker (e.g., Pepperstone-Live, Exness-MT5Trial)

# --- TRADING PARAMETERS ---
SYMBOL = "XAUUSD"                 # Asset you want to trade (Gold, EURUSD, etc.)
TIMEFRAME = mt5.TIMEFRAME_M15     # Chart timeframe (e.g., M15, M30, H1)
LOT_SIZE = 0.01                   # Position size

def initialize_mt5():
    """Initializes and logs into any broker terminal using standard MT5 credentials."""
    if not mt5.initialize():
        print(f"MT5 initialization failed. Error code: {mt5.last_error()}")
        return False
    
    # Authenticate with the broker server specified above
    authorized = mt5.login(
        login=ACCOUNT_LOGIN, 
        password=ACCOUNT_PASSWORD, 
        server=ACCOUNT_SERVER
    )
    
    if not authorized:
        print(f"Failed to connect to server '{ACCOUNT_SERVER}'. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print(f"Successfully connected! Logged into account {ACCOUNT_LOGIN} on server {ACCOUNT_SERVER}")
    return True

def calculate_adx_ema(df):
    """Calculates strategy indicators (EMAs and trend filters)."""
    df['EMA_Fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_Slow'] = df['close'].ewm(span=21, adjust=False).mean()
    return df

def execute_trade(signal_type):
    """Sends a market order to the connected broker."""
    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(f"Symbol {SYMBOL} not found.")
        return

    if not symbol_info.visible:
        if not mt5.symbol_select(SYMBOL, True):
            print(f"Failed to select symbol {SYMBOL}")
            return

    price = mt5.symbol_info_x(SYMBOL).ask if signal_type == "BUY" else mt5.symbol_info_x(SYMBOL).bid
    order_type = mt5.ORDER_TYPE_BUY if signal_type == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "DtayFxEngine Universal Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order execution failed, retcode={result.retcode}")
    else:
        print(f"Order executed successfully! Ticket ID: {result.order}")

def run_bot():
    if not initialize_mt5():
        return

    print(f"Starting execution loop for {SYMBOL}...")
    
    while True:
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
        if rates is None:
            print("Failed to fetch price data from broker. Retrying...")
            time.sleep(10)
            continue

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        df = calculate_adx_ema(df)
        
        last_candle = df.iloc[-2]
        prev_candle = df.iloc[-3]
        
        # Strategy trigger: Fast EMA crosses above Slow EMA
        if prev_candle['EMA_Fast'] <= prev_candle['EMA_Slow'] and last_candle['EMA_Fast'] > last_candle['EMA_Slow']:
            print("Bullish crossover signal detected. Executing BUY...")
            execute_trade("BUY")
            
        time.sleep(30)

if __name__ == "__main__":
    run_bot()
