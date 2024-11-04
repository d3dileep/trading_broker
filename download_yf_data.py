import yfinance as yf
import pandas as pd

def get_data(symbol, interval):
    # Downloading data using yfinance
    if interval in ['1m','2m']:
        period = "1d"
    elif interval in ['5m']:
        period = "5d"
    elif interval in ['15m']:
        period = "1mo"
    elif interval in ['30m']:
        period = "1mo"
    elif interval in ['1h','4h']:
        period = "1y"
    elif interval in ['1d','1wk']:
        period = "1y"
    try:
        if interval == '4h':
            interval= "1h"
            data = yf.download(symbol,  interval=interval, period=period, progress=False)
            data['Date'] = data.index
            data.reset_index(drop=True,inplace=True)
            df = data[["Date","Open", "High", "Low", "Close","Volume"]].copy()
            df = hourly_agg(df)
        else:
            data = yf.download(symbol, interval=interval, period=period, progress=False)
            data['Date'] = data.index
            data.reset_index(drop=True,inplace=True)
            df = data[["Date","Open", "High", "Low", "Close","Volume"]].copy()
    except Exception as e:
        period = "max"
        if interval == '4h':
            interval= "1h"
            data = yf.download(symbol,  interval=interval, period=period, progress=False)
            data['Date'] = data.index
            data.reset_index(drop=True,inplace=True)
            df = data[["Date","Open", "High", "Low", "Close","Volume"]].copy()
            df = hourly_agg(df)
        else:
            data = yf.download(symbol, interval=interval, period=period, progress=False)
            data['Date'] = data.index
            data.reset_index(drop=True,inplace=True)
            df = data[["Date","Open", "High", "Low", "Close","Volume"]].copy()
    return df
def hourly_agg(df):
    df.index = df['Date']# Group the data by day
    grouped = df.groupby(df.index.date)
    ohlc_4h = pd.DataFrame()
    # Resample each group to 4-hour intervals and aggregate to compute the 4-hourly OHLC data
    for group_name, group_data in grouped:
      resampled_data = group_data.resample('4h').agg({
          'Date':'first',
          'Open': 'first',       # First value in the 4-hour interval
          'High': 'max',         # Maximum value in the 4-hour interval
          'Low': 'min',          # Minimum value in the 4-hour interval
          'Close': 'last',        # Last value in the 4-hour interval
          'Volume': 'sum'
      })
      ohlc_4h = pd.concat([ohlc_4h, resampled_data])
    ohlc_4h = ohlc_4h.reset_index(drop=True)
    ohlc_4h.ffill( inplace=True)
    return ohlc_4h
