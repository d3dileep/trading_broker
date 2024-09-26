import os
import sys

# Change to the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import datetime
print(datetime.datetime.now())
from token1 import xts_data_token
from xts_class2 import XTS_parse
import configparser
import pandas as pd
import pandas_ta as ta
import time
import pytz
import datetime
import requests
from price_divergence import call_div_func
from nsepythonserver import *
import warnings
warnings.filterwarnings("ignore")


def nse_quote_ltp(symbol):
  payload = nse_quote(symbol)
  print(payload.keys())
  all_dict = dict()

  selected_key = next((key for key in payload["expiryDatesByInstrument"] if "futures" in key.lower()), None)
  all_dict["fut_latest_expiry"]= payload["expiryDatesByInstrument"][selected_key][0]
  all_dict["fut_next_expiry"]= payload["expiryDatesByInstrument"][selected_key][1]
  selected_key = next((key for key in payload["expiryDatesByInstrument"] if "options" in key.lower()), None)
  all_dict["option_latest_expiry"]= payload["expiryDatesByInstrument"][selected_key][0]
  all_dict["option_next_expiry"]= payload["expiryDatesByInstrument"][selected_key][1]
  all_dict["current_price"] = payload["underlyingValue"]

  return payload, all_dict
def send_to_telegram(message):
    token = '1242019168:AAGB9EVv01WkskLJf3DlFp7C_dNvwm1r21E'
    chat_id = '@chattel_test'
    # chat_id = '-1001663914038'
    #chat_id = '-1001246040635'
    # chat_id = '@chattel_nifty'
    print(message)
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'
    response = requests.get(url)
    return response

def check_buy(data, direction):
    if data["macd_stoch_rsi_sum_divergence"].iloc[-1] != 0:
        if data["macd_stoch_rsi_sum_divergence"].iloc[-1] == -1:
            return "Bearish"
   #     if data["macd_stoch_rsi_sum_divergence"].iloc[-1] == 1:
   #         return "Bullish"
    else:
        return None
    
def parse_custom_date(date_string):
  """Parses a date string in the format YY Mon DD into a datetime object using pandas."""
  parts = date_string.split()
  year, month, day = parts[0], parts[1], parts[2]
  formatted_date = f"{day}-{month}-{year}"
  return pd.to_datetime(formatted_date, format="%d-%b-%y")

def get_nearest_expiry(df_option, symbol, current_spot_price):
    # Convert EXPIRY to datetime if necessary
    df_option['EXPIRY'] = df_option["EXPIRY"].apply(parse_custom_date)

    # Filter options based on symbol and strike price (adjust filtering logic as needed)
    filtered_df = df_option[(df_option['DESCRIPTION'].str.contains(symbol)) &
                           (df_option['STRIKE'] == current_spot_price)]

    if filtered_df.empty:
        return None  # Handle case where no matching options found

    # Calculate time difference to today
    filtered_df['time_diff'] = (filtered_df['EXPIRY'] - pd.Timestamp('today')).dt.days

    # Get the index of the option with the smallest positive time difference
    nearest_expiry_index = filtered_df[filtered_df['time_diff'] >= 0]['time_diff'].idxmin()
    nearest_expiry = filtered_df.loc[nearest_expiry_index, 'EXPIRY']

    return nearest_expiry

def check_trailing_stop_loss(close_price, buy_price, stoploss):
    target_percentage = 1.0  # 100% target of buy_price

    target_price = buy_price * (1 + target_percentage)

    if close_price <= stoploss:
        print("stoploss hit ")
        return "Stoploss hit"
    elif close_price >= target_price:
        print("target achieved")
        return "Target achieved"
    else:
        return None

def round_down(value, base):
    """
    Round down to the nearest multiple of base.
    
    :param value: The value to be rounded down.
    :param base: The base to round down to.
    :return: The rounded down value.
    """
    return value - (value % base)

def round_up(value, base):
    """
    Round up to the nearest multiple of base.
    
    :param value: The value to be rounded up.
    :param base: The base to round up to.
    :return: The rounded up value.
    """
    return value + (base - (value % base)) if value % base != 0 else value

def generate_round_numbers(symbol, start):
    """
    Generate a list of round numbers around the start value based on the symbol.
    
    :param symbol: The symbol for which to generate round numbers (e.g., 'BANKNIFTY' or 'NIFTY')
    :param start: The starting value which is not a multiple of the rounding base
    :return: A list of round numbers around the start value
    """
    round_numbers = []
    
    if symbol == 'BANKNIFTY':
        base = 500
    elif symbol == 'NIFTY':
        base = 100
    else:
        raise ValueError("Unsupported symbol. Use 'BANKNIFTY' or 'NIFTY'.")

    lower_bound = round_down(start, base)
    upper_bound = round_up(start, base)

    # Generate round numbers: 3 below and 3 above
    for i in [-4,-3,-2,-1,1,2,3,4]:
        round_number = lower_bound + i * base
        if round_number >= 0:
            round_numbers.append(int(round_number))
    
    # Remove duplicates and sort the result
    round_numbers = sorted(set(round_numbers))

    return round_numbers

def get_dat_xts():

    try:
        cfg = configparser.ConfigParser()
        cfg.read("/home/ubuntu/trading_broker/data_{}.ini".format('bnf_buy'))
        xts= XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)
    except:
        cfg = configparser.ConfigParser()
        xts_data_token('1d6c9410fdb291b0a1d933','Toqb450@EN','bnf_buy')
        cfg.read("/home/ubuntu/trading_broker/data_{}.ini".format('bnf_buy'))
        xts= XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)

    segment = 2
    #symbol_list = ['BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'NIFTY', 'NIFTYNXT50']
    symbol_list = ["NIFTY","BANKNIFTY"]
    symbol = symbol_list[1]
    # Define IST timezone
    IST = pytz.timezone('Asia/Kolkata')

    # Define start and end times in IST
    start_time = datetime.time(8, 0, 0)
    end_time = datetime.time(15, 30, 0)

    # Get current time in IST
    current_time = datetime.datetime.now(IST).time()
    is_bought_ce = False
    is_bought_pe = False
    buy_price_ce = 0
    buy_price_pe = 0
    stoploss_ce = 0
    stoploss_pe = 0
    bought_symbol_id = dict()
    option_id = dict()
    # Find nearest expiry date
    for symbol in symbol_list:
      try:
        payload, all_dict = nse_quote_ltp(symbol)
        current_expiry = all_dict["option_latest_expiry"]
        current_expiry = current_expiry.replace("-","")
        next_expiry = all_dict["option_next_expiry"]
        next_expiry = next_expiry.replace("-","")
        expiry_list = [current_expiry, next_expiry]
        current_spot_price = all_dict["current_price"]
        strike_price_list = generate_round_numbers(symbol, current_spot_price)
        optiontype_list = ["CE","PE"]
        print(current_spot_price)
        print(expiry_list) 
        for expiry in expiry_list:
          for strike_price in strike_price_list:
            for optiontype in optiontype_list:
                try:
                    if ((strike_price > current_spot_price)&(optiontype == "CE"))|((strike_price < current_spot_price)&(optiontype == "PE")):
                        continue
                    response = xts.get_option_instrumentID(
                    exchangeSegment=2,
                    series='OPTIDX',
                    symbol=symbol,
                    expiryDate=expiry,
                    optionType=optiontype,
                    strikePrice=strike_price)
                    option_id[f'{symbol}{strike_price}{optiontype}{expiry}']= str(response["result"][0]["ExchangeInstrumentID"])
                except Exception as e:
                    print("No data",e, expiry, strike_price, optiontype)
                    
                    continue
      except:
          continue
    print(option_id)
    if current_time <= start_time:
        base_date = datetime.date.today()
        start_datetime = datetime.datetime.combine(base_date, start_time)
        current_datetime = datetime.datetime.combine(base_date, current_time)
        print(f"sleeping for {(start_datetime - current_datetime).total_seconds()} seconds")
        time.sleep((start_datetime - current_datetime).total_seconds())
    current_time = datetime.datetime.now(IST).time()
    i = 0
    while current_time >= start_time and current_time <= end_time:
      current_time = datetime.datetime.now(IST).time()
      for option_symbol, opt_id in option_id.items():
          try:
            df_ce, now = xts.read_data(opt_id, 300,segment, days=3)
            df_ce.rename(columns={'open': 'Open', 'close': 'Close','date':'Date','low':'Low','high':'High'}, inplace=True)
            df_ce.ta.macd(append=True)
            df_ce.ta.rsi(append=True)
            df_ce.ta.stoch(fastk_period=14, fastd_period=3, append=True)
            df_ce.dropna(inplace=True)
            df_ce.reset_index(inplace=True, drop=True)
            df_ce = call_div_func(df_ce)
            ltp = df_ce["Close"].iloc[-1]
            if (df_ce['RSI_14'].iloc[-20:].mean()>60)&((df_ce['macd_stoch_sum_divergence'].iloc[-1]== -1)|
                    (df_ce['macd_rsi_sum_divergence'].iloc[-1]== -1)|(df_ce['stoch_rsi_sum_divergence'].iloc[-1]== -1)):
                send_to_telegram(f"sell {option_symbol} @ {ltp}")
        
          # ['date', 'open', 'high', 'low', 'close', 'volume', 'oi', 'MACD_12_26_9','MACDh_12_26_9', 'MACDs_12_26_9', 'RSI_14', 'STOCHk_14_3_3','STOCHd_14_3_3']'macd_stoch_sum_divergence','macd_rsi_sum_divergence', 'stoch_rsi_sum_divergence','macd_stoch_rsi_sum_divergence'
            if i==0:
                send_to_telegram(f"Good Morning, starting Strategy run {current_time}")
                i+=1
            time.sleep(10)
          except Exception as e:
            print(option_symbol, e)
            continue
        
get_dat_xts()


