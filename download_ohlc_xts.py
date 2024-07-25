from token1 import xts_data_token
from xts_class2 import XTS_parse
import configparser
import pandas as pd
import pandas_ta as ta
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

def check_buy(df):
    last_row = df.iloc[-1]
    # Condition 1: RSI_14 to be upward and between 30 to 40
    condition1 = (last_row['RSI_14'] > df['RSI_14'].shift(1).iloc[-1]) & (last_row['RSI_14'] >= 30) & (last_row['RSI_14'] <= 40)
    # Condition 2: volume to be higher than avg_volume
    condition2 = last_row['volume'] > last_row['avg_volume']
    if condition1 & condition2:
        return True
    else:
        return False

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
    
def get_dat_xts(symbol, segment):

    try:
        cfg.read("data_{}.ini".format('bnf_buy'))
        xts= XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)
    except:
        cfg = configparser.ConfigParser()
        xts_data_token('1d6c9410fdb291b0a1d933','Toqb450@EN','bnf_buy')
        cfg.read("data_{}.ini".format('bnf_buy'))
        xts= XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)

    print(symbol)
    df_option, df_index, df_eq = xts.ExchangeInstrumentID()
    if segment ==1:
        if symbol in df_eq["SYMBOL"].to_list():
            symbol_id = df_eq[df_eq["SYMBOL"]==symbol]["EXCHANGEID"].values[0]
        if symbol in df_index["NAME OF COMPANY"].to_list():
            symbol_id = df_index[df_index["NAME OF COMPANY"]==symbol]["EXCHANGEID"].values[0]
    # Define IST timezone
    IST = pytz.timezone('Asia/Kolkata')

    # Define start and end times in IST
    start_time = datetime.time(9, 15, 0)
    end_time = datetime.time(15, 30, 0)

    # Get current time in IST
    current_time = datetime.datetime.now(IST).time()
    is_bought_ce = False
    is_bought_pe = False
    buy_price_ce = 0
    buy_price_pe = 0
    stoploss_ce = 0
    stoploss_pe = 0
    while current_time >= start_time and current_time <= end_time:
        current_time = datetime.datetime.now(IST).time()
        try:
            if segment ==2:
                index_df, _ = xts.read_data(26001, 300,1, days=3)
                current_spot_price = index_df["close"].iloc[-1]
                # Find nearest expiry date
                nearest_expiry = df_option.iloc[(pd.to_datetime(df_option['EXPIRY'], format='%d %b %y') - pd.to_datetime('today')).abs().argsort()[:1]]
                # Find at-the-money (ATM) strike price
                atm_strike = df_option.iloc[(df_option['STRIKE'] - current_spot_price).abs().argsort()[:1]]
                # print("Nearest expiry date:", nearest_expiry['EXPIRY'].values[0])
                # print("At-the-money (ATM) strike price:", atm_strike['STRIKE'].values[0])        
                # if symbol in  df_option["NAME OF OPTION"].to_list():
                df_filter = df_option[(df_option["NAME OF OPTION"].str.contains(symbol))&
                                    (df_option["STRIKE"]==atm_strike['STRIKE'].values[0])&
                                    (df_option["EXPIRY"]==nearest_expiry['EXPIRY'].values[0])]
                symbol_id_ce = df_filter["EXCHANGEID"].values[0]
                symbol_id_pe = df_filter["EXCHANGEID"].values[1]
            # print(symbol_id_ce, symbol_id_pe, segment)

            df_ce, now = xts.read_data(symbol_id_ce, 300,segment, days=3)
            df_ce.ta.rsi(append=True)
            df_ce["avg_volume"] = ta.sma(df_ce["volume"], length=20)
            df_ce.dropna(inplace=True)
            df_ce.reset_index(drop=True, inplace=True)
            close_price_ce = df_ce["close"].iloc[-1]
            if is_bought_ce:
                if stoploss_ce < close_price_ce * 0.8:
                    stoploss_ce = close_price_ce * 0.8
                checking_sell_ce = check_trailing_stop_loss(close_price_ce, buy_price_ce, stoploss_ce)
                if checking_sell_ce:
                    send_to_telegram("PE selling status" + checking_sell_ce + " @" + str(close_price_ce))
                    is_bought_ce = False
            else:
                is_bought_ce = check_buy(df_ce)
                buy_price_ce = df_ce["close"].iloc[-1]
                if is_bought_ce:
                    send_to_telegram("CE buying status"  + " @" + str(buy_price_ce))
            time.sleep(0.5)
            df_pe, now = xts.read_data(symbol_id_pe, 300,segment, days=3)
            df_pe.ta.rsi(append=True)
            df_pe["avg_volume"] = ta.sma(df_pe["volume"], length=20)
            df_pe.dropna(inplace=True)
            df_pe.reset_index(drop=True, inplace=True)
            close_price_pe = df_pe["close"].iloc[-1]
            if is_bought_pe:
                if stoploss_pe < close_price_pe * 0.8:
                    stoploss_pe = close_price_pe * 0.8
                checking_sell_pe = check_trailing_stop_loss(close_price_pe, buy_price_pe, stoploss_pe)
                if checking_sell_pe:
                    send_to_telegram("PE selling status" + checking_sell_pe + " @" + str(close_price_pe))
                    is_bought_pe = False
            else:
                is_bought_pe = check_buy(df_pe)
                buy_price_pe = df_pe["close"].iloc[-1]
                if is_bought_pe:
                    send_to_telegram("PE buying status"  + " @" + str(buy_price_pe))
            time.sleep(60)
        except Exception as e:
            print(e)
            continue
        
get_dat_xts('BANKNIFTY', 2)

