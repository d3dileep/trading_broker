import datetime
print(datetime.datetime.now())
from token2 import xts_data_token
from xts_class2 import XTS_parse
import configparser
import pandas as pd
import pandas_ta as ta
import os
import sys

# Change to the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
from option_div_new import round_down, round_up, generate_round_numbers
import time
import pytz
import datetime
import requests
import warnings
warnings.filterwarnings("ignore")
 
def send_to_telegram(message):
    token = '1242019168:AAGB9EVv01WkskLJf3DlFp7C_dNvwm1r21E'
    # chat_id = '@chattel_test'
    # chat_id = '-1001663914038'
    chat_id = '-1001246040635'
    # chat_id = '@chattel_nifty'
    print(message)
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'
    response = requests.get(url)
    return response

def check_buy(df, direction):
    last_row = df.iloc[-1]
    last_last_row = df.iloc[-2]
    # Condition 1: RSI_14 to be upward and between 30 to 40
    condition1 = (last_row['RSI_14'] > last_last_row['RSI_14']) & (last_row['RSI_14'] >= 30) & (last_row['RSI_14'] <= 40)
    # Condition 2: volume to be higher than avg_volume
    condition2 = last_row['volume'] > last_row['avg_volume']
    print(direction, condition1, condition2)
    if condition1 & condition2:
        return True
    else:
        return False
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

from nsepythonserver import *

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


def get_dat_xts():
    # Setup config and initialize XTS
    try:
        cfg = configparser.ConfigParser()
        cfg.read("/home/ubuntu/trading_broker/data1_{}.ini".format('bnf_buy'))
        xts = XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)
    except:
        cfg = configparser.ConfigParser()
        xts_data_token('85135d5e950fbc8b29d999', 'Vqhv461@eP', 'bnf_buy')
        cfg.read("/home/ubuntu/trading_broker/data1_{}.ini".format('bnf_buy'))
        xts = XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)

    segment = 2
    # Timezone and timing setup
    IST = pytz.timezone('Asia/Kolkata')
    start_time = datetime.time(9, 15, 0)
    end_time = datetime.time(15, 30, 0)
    current_time = datetime.datetime.now(IST).time()

    # Variables for tracking trades
    is_bought_ce, is_bought_pe = False, False
    buy_price_ce = buy_price_pe = stoploss_ce = stoploss_pe = 0
    bought_symbol_id_ce = bought_symbol_id_pe = None
    print("Fetching symbol")
    # Get symbols and expiries
    option_id = {}
    # symbol_list = ["NIFTY", "BANKNIFTY"]
    symbol_list = ['NIFTYNXT50', 'FINNIFTY', 'MIDCPNIFTY', 'BANKNIFTY', 'NIFTY']
    for symbol in symbol_list:
        try:
            payload, all_dict = nse_quote_ltp(symbol)
            current_expiry = all_dict["option_latest_expiry"].replace("-", "")
            next_expiry = all_dict["option_next_expiry"].replace("-", "")
            expiry_list = [current_expiry, next_expiry]
            current_spot_price = all_dict["current_price"]
            strike_price_list = generate_round_numbers(symbol, current_spot_price)
            print(all_dict)
            for expiry in expiry_list:
                for strike_price in strike_price_list:
                    for optiontype in ["CE", "PE"]:
                        try:
                            response = xts.get_option_instrumentID(
                                exchangeSegment=2,
                                series='OPTIDX',
                                symbol=symbol,
                                expiryDate=expiry,
                                optionType=optiontype,
                                strikePrice=strike_price
                            )
                            option_id[f'{symbol}{strike_price}{optiontype}{expiry}'] = str(response["result"][0]["ExchangeInstrumentID"])
                            print(f'extracted option ----> {str(response["result"][0]["ExchangeInstrumentID"])}')
                        except Exception as e:
                            print("No data", e, expiry, strike_price, optiontype)
                            continue
        except Exception as e:
            print("error", e)
            continue

    # Wait until start time
    if current_time <= start_time:
        print("sleeping")
        time.sleep((datetime.datetime.combine(datetime.date.today(), start_time) - datetime.datetime.combine(datetime.date.today(), current_time)).total_seconds())
    ce_symbol, pe_symbol = '', ''
    i = 0
    while start_time <= current_time <= end_time:
        current_time = datetime.datetime.now(IST).time()
        for option_symbol, opt_id in option_id.items():
            try:
                # Read CE/PE data based on the option type in opt_id
                #print(opt_id, segment)
                df, now = xts.read_data(opt_id, 300, segment, days=5)
                df.ta.ha(append=True)
                print(opt_id, segment, df.shape)
                df.drop(['open', 'high', 'low', 'close'], axis=1, inplace=True)
                df = df.rename(columns={'HA_open': 'open', 'HA_high': 'high', 'HA_low': 'low', 'HA_close': 'close'})
                df.ta.rsi(append=True)
                df["avg_volume"] = ta.sma(df["volume"], length=20)
                df.dropna(inplace=True)
                df.reset_index(drop=True, inplace=True)
                print(df.head())
                close_price = df["close"].iloc[-1]

                # Buy and sell conditions
                if "CE" in option_symbol:
                    if (is_bought_ce is True) and (ce_symbol == option_symbol):
                        if stoploss_ce < close_price * 0.8:
                            stoploss_ce = close_price * 0.8
                        if check_trailing_stop_loss(close_price, buy_price_ce, stoploss_ce):
                            send_to_telegram(f"CE selling status @ {close_price:.2f}")
                            is_bought_ce = False
                            stoploss_ce = 0
                    else:
                        is_bought_ce = check_buy(df, "CE buy check")
                        if is_bought_ce:
                            buy_price_ce = close_price
                            ce_symbol = option_symbol
                            send_to_telegram(f"{option_symbol} buying status @ {buy_price_ce:.2f}")

                elif "PE" in option_symbol:
                    if (is_bought_pe is True) and (pe_symbol == option_symbol):
                        if stoploss_pe < close_price * 0.8:
                            stoploss_pe = close_price * 0.8
                        if check_trailing_stop_loss(close_price, buy_price_pe, stoploss_pe):
                            send_to_telegram(f"PE selling status @ {close_price:.2f}")
                            is_bought_pe = False
                            stoploss_pe = 0
                            
                    else:
                        is_bought_pe = check_buy(df, "PE buy check")
                        if is_bought_pe:
                            buy_price_pe = close_price
                            pe_symbol = option_symbol
                            send_to_telegram(f"{option_symbol} buying status @ {buy_price_pe:.2f}")

                # Initial strategy start message
                if i == 0:
                    send_to_telegram("Good Morning, starting Strategy run")
                    i += 1
                
                time.sleep(60)
            except Exception as e:
                print(option_symbol, e)
                continue

get_dat_xts()
