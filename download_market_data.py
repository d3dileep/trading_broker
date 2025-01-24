import os
import sys
import pandas as pd

# Change to the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from download_yf_data import get_data
symbol_dict = {'NIFTY':'^NSEI','NIFTYBANK':'^NSEBANK','RELIANCE':'RELIANCE.NS'}
for index, symbol in symbol_dict.items():
  for interval in ['1m','5m']:
    try:
        df_new = get_data(symbol, interval = interval)
    except Exception as e:
        print('Error',e)
        continue
    if  df_new.shape[0]==0:
        print('Empty data')
        continue
    # Define the file path based on the index name
    file_path = f"/home/ubuntu/trading_broker/market_data/{index}_{interval}.csv"

    if os.path.exists(file_path):
        # Load existing data from CSV
        df_existing = pd.read_csv(file_path)

        # Ensure both dataframes have Date as a datetime type
        df_existing['Date'] = pd.to_datetime(df_existing['Date'])
        df_new['Date'] = pd.to_datetime(df_new['Date'])

        # Remove rows from df_new where Date is already in df_existing
        df_new = df_new[~df_new['Date'].isin(df_existing['Date'])]

        # Append new data to existing data
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        # If file does not exist, just save the new data
        df_combined = df_new

    # Save combined data back to CSV without index
    df_combined.to_csv(file_path, index=False)
    print(f"Updated data saved to {file_path}")
