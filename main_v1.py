from Connect import XTSConnect
import indicators
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
import requests
import io
import math
from time import sleep
import traceback

pd.set_option('display.max_columns', None)


def rounddown( x, y):
    return int(math.floor(x / y)) * y

def roundup(x,y):
    return int(math.ceil(x / y)) * y

def instr_id(xt, symbol, opt_type, exp_date, price):
    dict1 = {}
    if opt_type == 'PE':
        price = roundup(price,100)
    if opt_type == 'CE':
        price = rounddown(price, 100)
    response = xt.get_option_symbol(
        exchangeSegment=2,
        series='OPTIDX',
        symbol=symbol,
        expiryDate=exp_date,
        optionType=opt_type,
        strikePrice=price)['result'][0]
    return ('{}'.format(response['Description']), response['ExchangeInstrumentID'],price, opt_type)


def get_instr_list():
    nsefo_instr_url = 'http://public.fyers.in/sym_details/NSE_FO.csv'
    s = requests.get(nsefo_instr_url).content
    fo_instr = pd.read_csv(io.StringIO(s.decode('utf-8')), header=None)
    fo_instr[1] = fo_instr[1].apply(lambda x: x.upper())

    return fo_instr

def get_ohlc(xt, exchange, symbol, start, end, interval):
    start = start.strftime("%b %d %Y %H%M%S")
    end = end.strftime("%b %d %Y %H%M%S")
    data = xt.get_ohlc(
        exchangeSegment=exchange,
        exchangeInstrumentID=symbol,
        startTime=start,
        endTime=end,
        compressionValue=interval)['result']['dataReponse']
    result = [x.strip() for x in data.split(',')]
    value = []
    for item in result:
        data = [x.strip() for x in item.split('|')]
        value.append(data)
    data = pd.DataFrame(value, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'oi', 'red'])[
        ['date', 'open', 'high', 'low', 'close', 'oi']]
    data['date'] = pd.to_datetime(data['date'], unit='s')
    cols = [ 'open', 'high', 'low', 'close', 'oi']
    data[cols] = data[cols].apply(pd.to_numeric, errors='coerce')
    return data

def trade(name):
    """Investor client login credentials"""
    API_KEY = "85135d5e950fbc8b29d999"
    API_SECRET = "Vqhv461@eP"
    XTS_API_BASE_URL = "https://xts.compositedge.com"
    source = "WEBAPI"

    """Make the XTSConnect Object with Marketdata API appKey, secretKey and source"""
    xt = XTSConnect(API_KEY, API_SECRET, source)
    """Using the object we call the login function Request"""
    response = xt.marketdata_login()
    """Get Config Request"""
    response = xt.get_config()

    fo_instr_list = get_instr_list()
    all_expiries = sorted(list(set([datetime.strptime(str(x)[4:10], '%y%m%d') for x in fo_instr_list[0].tolist()])))
    all_expiries_trunc = [item.strftime("%d%b%Y") for item in all_expiries[:6] if item.weekday() in [2,3]]


    """Get OHLC Request"""
    tzinfo = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz=tzinfo)
    today = now.date()
    from_days = 5
    from_d = datetime.combine(today - timedelta(days=from_days), time(9, 15, 00))

    if name == 'BANKNIFTY':
        symbol = 26001
    if name == 'NIFTY':
        symbol = 26000
    # NSECM, NSEFO for fut/option
    call_buy = True
    put_buy = True
    display = False
    trade_list =[]
    while datetime.now(tz=tzinfo).time() < time(15, 30, 0):
        sleep(2)
        now = datetime.now(tz=tzinfo)  # tz= tzinf
        current_time = time(now.hour, now.minute, now.second)
        to_d = datetime.combine(today, current_time)
        try:
            nse_data = get_ohlc(xt, 'NSECM', symbol, from_d, to_d, 600)
            nse_data['rsi'] = indicators.rsi(nse_data)
            nse_data = indicators.madrid_ribbon(nse_data)
            nse_data = indicators.squeeze_momentum(nse_data)
        except Exception as e:
            print(e, datetime.now(tz=tzinfo), symbol)
            continue
        data = nse_data.iloc[-100:, :]
        latest_price = data.close[-1:].values[0]
        if datetime.now(tz=tzinfo).minute % 2 != 0:
            display = True
        if datetime.now(tz=tzinfo).minute % 10 == 0 and display==True:
            print(datetime.now(tz=tzinfo), name, latest_price, data.rsi[-1:].values[0], data.rsi[-2:-1].values[0], data.value[-2:-1].values[0], data.value[-3:-2].values[0])
            display=False
        if data.rsi[-1:].values[0] <45 and data.rsi[-1:].values[0] > data.rsi[-2:-1].values[0] and \
                data.rsi[-2:-1].values[0] > data.rsi[-3:-2].values[0] and \
                data.value[-2:-1].values[0] > data.value[-3:-2].values[0] and call_buy ==True:
            dat1 = instr_id(xt, name, 'CE', all_expiries_trunc[0], latest_price)
            try:
                opt_data = get_ohlc(xt, 'NSEFO', dat1[1], from_d, to_d, 3600)
                current_price = opt_data['close'][-1:].values[0]
            except Exception as e:
                print(e, datetime.now(tz=tzinfo), dat1[0])
                continue
            buy_price = current_price
            print( name, latest_price, 'buy CE', dat1[0], buy_price )
            trade_list.append((name, latest_price, 'buy CE', dat1[0], buy_price))
            call_buy= False

        if call_buy== False:
            try:
                opt_data = get_ohlc(xt, 'NSEFO', dat1[1], from_d, to_d, 3600)
                current_price = opt_data['close'][-1:].values[0]
            except Exception as e:
                print(e, datetime.now(tz=tzinfo), dat1[0])
                continue
            if buy_price > 1.05 * current_price or buy_price < 0.95 * current_price:
                print(name, latest_price, 'sell CE', dat1[0], current_price)
                trade_list.append((name, latest_price, 'sell CE', dat1[0], current_price))
                call_buy = True

        if data.rsi[-1:].values[0] > 55 and data.rsi[-1:].values[0] < data.rsi[-2:-1].values[0] \
                and data.rsi[-2:-1].values[0] < data.rsi[-3:-2].values[0] and \
                data.value[-2:-1].values[0] < data.value[-3:-2].values[0] and put_buy == True:
            dat1 = instr_id(xt, name, 'PE', all_expiries_trunc[0], latest_price )
            try:
                opt_data = get_ohlc(xt, 'NSEFO', dat1[1], from_d, to_d, 3600)
                current_price = opt_data['close'][-1:].values[0]
            except Exception as e:
                print(e, datetime.now(tz=tzinfo), dat1[0])
                continue
            buy_price = current_price
            print(name, latest_price, 'buy PE', dat1[0], buy_price)
            trade_list.append((name, latest_price, 'buy PE', dat1[0], buy_price))
            put_buy = False

        if put_buy == False:
            try:
                opt_data = get_ohlc(xt, 'NSEFO', dat1[1], from_d, to_d, 3600)
                current_price = opt_data['close'][-1:].values[0]
            except Exception as e:
                print(e, datetime.now(tz=tzinfo), dat1[0])
                continue
            if buy_price > 1.05 * current_price or buy_price < 0.95 * current_price:
                print(name, latest_price, 'sell PE', dat1[0], current_price)
                trade_list.append((name, latest_price, 'sell PE', dat1[0], current_price))
                put_buy = True

    print(trade_list)
    """to get option symbols"""
    # diff_price = roundup(latest_price * 0.005, 100)
    # price1 = [latest_price - diff_price * item for item in [0, 1, 2, 3, 4]]
    # price2 = [latest_price + diff_price * item for item in [0, 1, 2, 3, 4]]
    # prices = sorted(list(set(price1 + price2)))
    #
    # ins_id = []
    # for exp in all_expiries_trunc:
    #     for price in prices:
    #         for type1 in ['CE', 'PE']:
    #             dat1 = instr_id(xt, name, type1, exp, price)
    #             ins_id.append(dat1)
    # for instr in ins_id:
    #     try:
    #         print(instr[0])
    #         data = get_ohlc(xt, 'NSEFO', instr[1], from_d, to_d, 3600)
    #         print(data.tail(1))
    #     except Exception as e:
    #         print(instr[0], e)
    #         continue


if __name__ == '__main__':
    trade('BANKNIFTY')
