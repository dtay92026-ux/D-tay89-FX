import time
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import requests  # Required for sending Telegram HTTP requests

# ==========================================
# UNIVERSAL BROKER CONFIGURATION
# ==========================================
ACCOUNT_LOGIN = 12345678  # Your Account Number (Login ID)
ACCOUNT_PASSWORD = "YourPassword"  # Your Trading Account Password
ACCOUNT_SERVER = "Broker-Server"  # Exact Server Name provided by your broker

# ==========================================
# TELEGRAM CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = (
    "YOUR_BOT_TOKEN_FROM_BOTFATHER"  # Paste your token here inside the quotes
)
TELEGRAM_CHAT_ID = (
    "YOUR_CHAT_ID"  # Your personal Telegram user ID or chat/channel ID
)

# --- TRADING PARAMETERS ---
SYMBOL = "XAUUSD"  # Asset you want to trade (Gold, EURUSD, etc.)
TIMEFRAME = mt5.TIMEFRAME_M15  # Chart timeframe (e.g., M15, M30, H1)
LOT_SIZE = 0.01  # Position size


def send_telegram_message(message):
  """Sends a notification message to your Telegram chat."""
  if (
      TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_FROM_BOTFATHER"
      or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID"
  ):
    print("Telegram token or Chat ID not configured yet.")
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    if not response.json().get("ok"):
      print(f"Telegram API Error: {response.json().get('description')}")
  except Exception as e:
    print(f"Failed to send Telegram message: {e}")


def initialize_mt5():
  """Initializes and logs into any broker terminal using standard MT5 credentials."""
  if not mt5.initialize():
    error_msg = f"MT5 initialization failed. Error code: {mt5.last_error()}"
    print(error_msg)
    send_telegram_message(f"🚨 *DtayFxEngine Alert*\n{error_msg}")
    return False

  authorized = mt5.login(
      login=ACCOUNT_LOGIN, password=ACCOUNT_PASSWORD, server=ACCOUNT_SERVER
  )

  if not authorized:
    error_msg = f"Failed to connect to server '{ACCOUNT_SERVER}'. Error code: {mt5.last_error()}"
    print(error_msg)
    send_telegram_message(f"🚨 *DtayFxEngine Alert*\n{error_msg}")
    mt5.shutdown()
    return False

  success_msg = (
      f"Successfully connected! Logged into account {ACCOUNT_LOGIN} on server"
      f" {ACCOUNT_SERVER}"
  )
  print(success_msg)
  send_telegram_message(
      f"✅ *DtayFxEngine Connected*\nAccount: `{ACCOUNT_LOGIN}`\nSymbol:"
      f" `{SYMBOL}`"
  )
  return True


def calculate_adx_ema(df):
  """Calculates strategy indicators (EMAs and trend filters)."""
  df["EMA_Fast"] = df["close"].ewm(span=9, adjust=False).mean()
  df["EMA_Slow"] = df["close"].ewm(span=21, adjust=False).mean()
  return df


def execute_trade(signal_type):
  """Sends a market order to the connected broker and alerts Telegram."""
  symbol_info = mt5.symbol_info(SYMBOL)
  if symbol_info is None:
    print(f"Symbol {SYMBOL} not found.")
    return

  if not symbol_info.visible:
    if not mt5.symbol_select(SYMBOL, True):
      print(f"Failed to select symbol {SYMBOL}")
      return

  price = (
      mt5.symbol_info_x(SYMBOL).ask
      if signal_type == "BUY"
      else mt5.symbol_info_x(SYMBOL).bid
  )
  order_type = (
      mt5.ORDER_TYPE_BUY if signal_type == "BUY" else mt5.ORDER_TYPE_SELL
  )

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
    error_msg = (
        f"❌ *Order Execution Failed*\nSymbol: `{SYMBOL}`\nRetcode:"
        f" `{result.retcode}`"
    )
    print(error_msg)
    send_telegram_message(error_msg)
  else:
    success_msg = (
        f"🚀 *Trade Executed Successfully!* ({signal_type})\nSymbol:"
        f" `{SYMBOL}`\nVolume: `{LOT_SIZE}`\nPrice: `{price}`\nTicket ID:"
        f" `{result.order}`"
    )
    print(success_msg)
    send_telegram_message(success_msg)


def run_bot():
  if not initialize_mt5():
    return

  print(f"Starting execution loop for {SYMBOL}...")
  send_telegram_message(f"🔄 *DtayFxEngine Loop Started* for `{SYMBOL}`")

  while True:
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    if rates is None:
      print("Failed to fetch price data from broker. Retrying...")
      time.sleep(10)
      continue

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")

    df = calculate_adx_ema(df)

    last_candle = df.iloc[-2]
    prev_candle = df.iloc[-3]

    # Strategy trigger: Fast EMA crosses above Slow EMA
    if (
        prev_candle["EMA_Fast"] <= prev_candle["EMA_Slow"]
        and last_candle["EMA_Fast"] > last_candle["EMA_Slow"]
    ):
      signal_msg = (
          f"📈 *Bullish Crossover Signal Detected* on `{SYMBOL}`! Executing BUY..."
      )
      print(signal_msg)
      send_telegram_message(signal_msg)
      execute_trade("BUY")

    time.sleep(30)


if __name__ == "__main__":
  run_bot()
