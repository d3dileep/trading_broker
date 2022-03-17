import numpy as np
import pandas as pd
import pandas_ta as ta

def squeeze_momentum(df):
  # parameter setup (default values in the original indicator)
  length = 20
  mult = 2
  length_KC = 20
  mult_KC = 1.5

  # calculate Bollinger Bands
  # moving average
  m_avg = df['close'].rolling(window=length).mean()
  # standard deviation
  m_std = df['close'].rolling(window=length).std(ddof=0)
  # upper Bollinger Bands
  df['upper_BB'] = m_avg + mult * m_std
  # lower Bollinger Bands
  df['lower_BB'] = m_avg - mult * m_std

  # calculate Keltner Channel
  # first we need to calculate True Range
  df['tr0'] = abs(df["high"] - df["low"])
  df['tr1'] = abs(df["high"] - df["close"].shift())
  df['tr2'] = abs(df["low"] - df["close"].shift())
  df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
  # moving average of the TR
  range_ma = df['tr'].rolling(window=length_KC).mean()
  # upper Keltner Channel
  df['upper_KC'] = m_avg + range_ma * mult_KC
  # lower Keltner Channel
  df['lower_KC'] = m_avg - range_ma * mult_KC

  # calculate bar value
  highest = df['high'].rolling(window = length_KC).max()
  lowest = df['low'].rolling(window = length_KC).min()
  m1 = (highest + lowest)/2
  df['value'] = (df['close'] - (m1 + m_avg)/2)
  fit_y = np.array(range(0,length_KC))
  df['value'] = df['value'].rolling(window = length_KC).apply(lambda x:
                            np.polyfit(fit_y, x, 1)[0] * (length_KC-1) +
                            np.polyfit(fit_y, x, 1)[1], raw=True)
  # df['value'] = df['value'] * 100 / df['value'].max()
  # check for 'squeeze'
  df['squeeze_on'] = (df['lower_BB'] > df['lower_KC']) & (df['upper_BB'] < df['upper_KC'])
  df['squeeze_off'] = (df['lower_BB'] < df['lower_KC']) & (df['upper_BB'] > df['upper_KC'])
  return df


def support_resistance(df):
  r1 = df['high'][-20:-5].sort_values(ascending=True)[-2:].mean()
  r2 = df['high'][-60:-20].sort_values(ascending=True)[-2:].mean()
  r3 = df['high'][-100:-60].sort_values(ascending=True)[-2:].mean()
  resistance_list = list([r1, r2, r3])
  s1 = df['low'][-20:-5].sort_values(ascending=False)[-2:].mean()
  s2 = df['low'][-60:-20].sort_values(ascending=False)[-2:].mean()
  s3 = df['low'][-100:-60].sort_values(ascending=False)[-2:].mean()
  list_all = list([s1, s2, s3]) + resistance_list
  list_all.sort()
  print(list_all)
  return list_all[0], list_all[1], list_all[2], list_all[3], list_all[4], list_all[5]

def delta(df):
  df = df[['open', 'high', 'low',	'close']]
  x = df.to_numpy()
  x = x.flatten()
  min = x.min()
  max = x.max()
  # Compute frequency and bins
  frequency, bins = np.histogram(x, bins=40, range=[min, max])
  dat = pd.DataFrame({'freq': frequency, 'bins': bins[1:]}).sort_values('freq')
  return dat

def rsi(df):
  return ta.sma(ta.rsi(df['close']),14)

def madrid_ribbon(df):
  df['ema_5'] = ta.ema(df['close'],5)
  df['ema_10'] = ta.ema(df['close'],10)
  df['ema_15'] = ta.ema(df['close'],15)
  df['ema_20'] = ta.ema(df['close'],20)
  df['ema_25'] = ta.ema(df['close'],25)
  df['ema_30'] = ta.ema(df['close'],30)
  df['ema_35'] = ta.ema(df['close'],35)
  df['ema_40'] = ta.ema(df['close'],40)
  df['ema_45'] = ta.ema(df['close'],45)
  df['ema_50'] = ta.ema(df['close'],50)
  df['ema_55'] = ta.ema(df['close'],55)
  df['ema_60'] = ta.ema(df['close'],60)
  df['ema_65'] = ta.ema(df['close'],65)
  df['ema_70'] = ta.ema(df['close'],70)
  df['ema_75'] = ta.ema(df['close'],75)
  df['ema_80'] = ta.ema(df['close'],80)
  df['ema_85'] = ta.ema(df['close'],85)
  df['ema_90'] = ta.ema(df['close'],90)
  df['ema_95'] = ta.ema(df['close'],95)
  df['ema_100'] = ta.ema(df['close'],100)
  df['ema_120'] = ta.ema(df['close'],120)
  df['ema_150'] = ta.ema(df['close'],150)

  return df
