## main divergence code
import pandas as pd
import numpy as np
import pandas_ta as ta
import warnings
warnings.filterwarnings("ignore")

def calculate_bullish_divergence(data, macd_column, window, name = "macd"):

  # Find index of lowest MACD value in the window
  lowest_macd_index = data[macd_column].rolling(window=window).apply(lambda x: x.idxmin())
  lowest_macd_index.dropna(inplace=True)
  # Get close price corresponding to lowest MACD value
  lowest_macd_close = data['Close'].loc[lowest_macd_index]

  # Find index of lowest close price in the window
  lowest_close_index = data['Close'].rolling(window=window).apply(lambda x: x.idxmin())
  lowest_close_index.dropna(inplace=True)
  # Get MACD value corresponding to lowest close price
  lowest_close_macd = data[macd_column].loc[lowest_close_index]

  # Create divergence column
  data[f'{name}_bullish_divergence_{window}'] = 0
  if name == "macd":
    cutoff = 0
  elif name == "rsi":
    cutoff = 70
  elif name == "stoch":
    cutoff = 80
  divergence_condition = (lowest_close_index > lowest_macd_index) & (data[macd_column].diff() > 0) & (data[macd_column] < cutoff)
  data.loc[divergence_condition, f'{name}_bullish_divergence_{window}'] = 1

  return data

def calculate_bearish_divergence(data, macd_column, window, name="macd"):
    # Find index of highest MACD value in the window
    highest_macd_index = data[macd_column].rolling(window=window).apply(lambda x: x.idxmax())
    highest_macd_index.dropna(inplace=True)
    # Get close price corresponding to highest MACD value
    highest_macd_close = data['Close'].loc[highest_macd_index]

    # Find index of highest close price in the window
    highest_close_index = data['Close'].rolling(window=window).apply(lambda x: x.idxmax())
    highest_close_index.dropna(inplace=True)
    # Get MACD value corresponding to highest close price
    highest_close_macd = data[macd_column].loc[highest_close_index]

    # Create divergence column
    data[f'{name}_bearish_divergence_{window}'] = 0
    if name == "macd":
        cutoff = 0
    elif name == "rsi":
        cutoff = 30  # Adjusted for bearish divergence in RSI (typically below 30)
    elif name == "stoch":
        cutoff = 20  # Adjusted for bearish divergence in Stochastic (typically below 20)

    # Define bearish divergence condition
    divergence_condition = (highest_close_index > highest_macd_index) & (data[macd_column].diff() < 0) & (data[macd_column] > cutoff)
    data.loc[divergence_condition, f'{name}_bearish_divergence_{window}'] = 1

    return data

def sum_and_delete_divergence_columns(df):
    # Sum macd_bullish columns
    macd_bullish_columns = [col for col in df.columns if col.startswith('macd_bullish_divergence')]
    df['macd_bullish_sum'] = df[macd_bullish_columns].sum(axis=1)
    df.drop(macd_bullish_columns, axis=1, inplace=True)

    # Sum rsi_bullish columns
    rsi_bullish_columns = [col for col in df.columns if col.startswith('rsi_bullish_divergence')]
    df['rsi_bullish_sum'] = df[rsi_bullish_columns].sum(axis=1)
    df.drop(rsi_bullish_columns, axis=1, inplace=True)

    # Sum stoch_bullish columns
    stoch_bullish_columns = [col for col in df.columns if col.startswith('stoch_bullish_divergence')]
    df['stoch_bullish_sum'] = df[stoch_bullish_columns].sum(axis=1)
    df.drop(stoch_bullish_columns, axis=1, inplace=True)

    # Sum macd_bearish columns
    macd_bearish_columns = [col for col in df.columns if col.startswith('macd_bearish_divergence')]
    df['macd_bearish_sum'] = df[macd_bearish_columns].sum(axis=1)
    df.drop(macd_bearish_columns, axis=1, inplace=True)

    # Sum rsi_bearish columns
    rsi_bearish_columns = [col for col in df.columns if col.startswith('rsi_bearish_divergence')]
    df['rsi_bearish_sum'] = df[rsi_bearish_columns].sum(axis=1)
    df.drop(rsi_bearish_columns, axis=1, inplace=True)

    # Sum stoch_bearish columns
    stoch_bearish_columns = [col for col in df.columns if col.startswith('stoch_bearish_divergence')]
    df['stoch_bearish_sum'] = df[stoch_bearish_columns].sum(axis=1)
    df.drop(stoch_bearish_columns, axis=1, inplace=True)

    return df

def call_div_func(data):

    data = calculate_bullish_divergence(data, "MACD_12_26_9", 30, "macd")
    data = calculate_bullish_divergence(data, "MACD_12_26_9", 60, "macd")
    data = calculate_bullish_divergence(data, "MACD_12_26_9", 90, "macd")
    data = calculate_bullish_divergence(data, "MACD_12_26_9", 120, "macd")

    data = calculate_bullish_divergence(data, "RSI_14", 15, "rsi")
    data = calculate_bullish_divergence(data, "RSI_14", 30, "rsi")
    data = calculate_bullish_divergence(data, "RSI_14", 45, "rsi")
    data = calculate_bullish_divergence(data, "RSI_14", 60, "rsi")

    data = calculate_bullish_divergence(data, "STOCHk_14_3_3", 15, "stoch")
    data = calculate_bullish_divergence(data, "STOCHk_14_3_3", 30, "stoch")
    data = calculate_bullish_divergence(data, "STOCHk_14_3_3", 45, "stoch")
    data = calculate_bullish_divergence(data, "STOCHk_14_3_3", 60, "stoch")

    data = calculate_bearish_divergence(data, "MACD_12_26_9", 30, "macd")
    data = calculate_bearish_divergence(data, "MACD_12_26_9", 60, "macd")
    data = calculate_bearish_divergence(data, "MACD_12_26_9", 90, "macd")
    data = calculate_bearish_divergence(data, "MACD_12_26_9", 120, "macd")

    data = calculate_bearish_divergence(data, "RSI_14", 15, "rsi")
    data = calculate_bearish_divergence(data, "RSI_14", 30, "rsi")
    data = calculate_bearish_divergence(data, "RSI_14", 45, "rsi")
    data = calculate_bearish_divergence(data, "RSI_14", 60, "rsi")

    data = calculate_bearish_divergence(data, "STOCHk_14_3_3", 15, "stoch")
    data = calculate_bearish_divergence(data, "STOCHk_14_3_3", 30, "stoch")
    data = calculate_bearish_divergence(data, "STOCHk_14_3_3", 45, "stoch")
    data = calculate_bearish_divergence(data, "STOCHk_14_3_3", 60, "stoch")

    data = sum_and_delete_divergence_columns(data)

    # Create a new column 'sum_divergence' and initialize it with zeros
    data['macd_stoch_sum_divergence'] = 0
    # Set the value of 'sum_divergence' to the sum of the two columns where both are non-zero
    data.loc[((data['macd_bullish_sum'] != 0) & (data['stoch_bullish_sum'] != 0)), 'macd_stoch_sum_divergence'] = 1
    data.loc[((data['macd_bearish_sum'] != 0) & (data['stoch_bearish_sum'] != 0)), 'macd_stoch_sum_divergence'] = -1

    # Create a new column 'sum_divergence' and initialize it with zeros
    data['macd_rsi_sum_divergence'] = 0
    # Set the value of 'sum_divergence' to the sum of the two columns where both are non-zero
    data.loc[((data['macd_bullish_sum'] != 0) & (data['rsi_bullish_sum'] != 0)), 'macd_rsi_sum_divergence'] = 1
    data.loc[((data['macd_bearish_sum'] != 0) & (data['rsi_bearish_sum'] != 0)), 'macd_rsi_sum_divergence'] = -1

    # Create a new column 'sum_divergence' and initialize it with zeros
    data['stoch_rsi_sum_divergence'] = 0
    # Set the value of 'sum_divergence' to the sum of the two columns where both are non-zero
    data.loc[((data['stoch_bullish_sum'] != 0) & (data['rsi_bullish_sum'] != 0)), 'stoch_rsi_sum_divergence'] = 1
    data.loc[((data['stoch_bearish_sum'] != 0) & (data['rsi_bearish_sum'] != 0)), 'stoch_rsi_sum_divergence'] = -1

  # Create a new column 'sum_divergence' and initialize it with zeros
    data['macd_stoch_rsi_sum_divergence'] = 0
    # Set the value of 'sum_divergence' to the sum of the two columns where both are non-zero
    data.loc[((data['stoch_bullish_sum'] != 0) & (data['rsi_bullish_sum'] != 0) & (data['macd_bearish_sum'] != 0)), 'macd_stoch_rsi_sum_divergence'] = 1
    data.loc[((data['stoch_bearish_sum'] != 0) & (data['rsi_bearish_sum'] != 0) & (data['macd_bearish_sum'] != 0)), 'macd_stoch_rsi_sum_divergence'] = -1

    return data
