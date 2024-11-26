from price_divergence_index import call_div_func
from download_yf_data import get_data
import pandas_ta as ta
import pandas as pd
import traceback
import time
import requests
import pytz
import datetime

def send_to_telegram(message):
    token = '1242019168:AAGB9EVv01WkskLJf3DlFp7C_dNvwm1r21E'
    # chat_id = '@chattel_test'
    # chat_id = '-1001663914038'
    #chat_id = '-1001246040635'
    chat_id = '@chattel_nifty'
    print(message)
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'
    response = requests.get(url)
    return response

def main_index():
    capture_list = []
    nifty = ['^NSEI', '^NSEBANK','NIFTY_FIN_SERVICE.NS','NIFTY_MID_SELECT.NS'] #+ nifty
    index_map = {"^NSEI":"NIFTY50","^NSEBANK":"BANKNIFTY","NIFTY_FIN_SERVICE.NS":"NIFTY FIN SERVICE", "NIFTY_MID_SELECT.NS":"NIFTY MID SELECT"}
    # Define IST timezone
    IST = pytz.timezone('Asia/Kolkata')
    # Define start and end times in IST
    start_time = datetime.time(9, 15, 0)
    end_time = datetime.time(15, 30, 0)
    # Get current time in IST
    current_time = datetime.datetime.now(IST).time()
    duration = [('5m','5d'),('15m','5d'),('30m','1mo'),('1h','6mo'),('4h','6mo'),("1d","1y")]
    if current_time <= start_time:
        base_date = datetime.date.today()
        start_datetime = datetime.datetime.combine(base_date, start_time)
        current_datetime = datetime.datetime.combine(base_date, current_time)
        print(f"sleeping for {(start_datetime - current_datetime).total_seconds()} seconds")
        time.sleep((start_datetime - current_datetime).total_seconds())
    current_time = datetime.datetime.now(IST).time()
    send_to_telegram("Lets Monitor the market")
    while current_time >= start_time and current_time <= end_time:
        current_time = datetime.datetime.now(IST).time()
        for symbol in nifty:
          for item in duration:
            try:
                interval = item[0]
                period = item[1]
                if not current_time.minute % 5 == 0 and interval == "5m":
                    continue
                if not current_time.minute % 15 == 0 and interval == "15m":
                    continue
                if not current_time.minute % 30 == 0 and interval == "30m":
                    continue
                if not current_time.minute % 59 == 0 and interval in ["1h","4h","1d"]:
                    continue
                try:
                    data_small_int_1h = get_data(symbol, interval=interval)
                    data = data_small_int_1h.copy()
                except:
                    data_small_int_1h = get_data(symbol, interval=interval)
                    data = data_small_int_1h.copy()
                data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                data.ta.macd(append=True)
                data.ta.rsi(append=True)
                data.ta.stoch(fastk_period=14, fastd_period=3, append=True)
                data.dropna(inplace=True)
                data.reset_index(inplace=True, drop=True)
                data = call_div_func(data)
                if data["macd_stoch_rsi_sum_divergence"].iloc[-1] != 0:
                    if data["macd_stoch_rsi_sum_divergence"].iloc[-1] == -1:
                        send_to_telegram(f"{index_map[symbol]} with interval {item[0]} showing Bearish @ {data['Close'].iloc[-1]}")
                    if data["macd_stoch_rsi_sum_divergence"].iloc[-1] == 1:
                        send_to_telegram(f"{index_map[symbol]} with interval {item[0]} showing Bullish @ {data['Close'].iloc[-1]}")
                    capture_list.append([symbol, item, data["macd_stoch_rsi_sum_divergence"].iloc[-1]])
                print(f'{symbol} for interval {item} with data len {datetime.datetime.now()}')
                time.sleep(1)
            except Exception as e:
                print(f"Error processing {symbol} {item}: {traceback.format_exc()} at time {datetime.datetime.now(IST)}")
                continue
        
        time.sleep(60)
main_index()
