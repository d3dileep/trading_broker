import pandas as pd

df = pd.read_csv("/home/ubuntu/trading_broker/market_data/NIFTY_1m.csv")
print(df.columns,df.shape)

# Define the main columns to consolidate duplicates into
main_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

# Step 1: Loop through each target column, find duplicates, and combine them
for col in main_columns:
    # Find all columns that start with the target column name, handling string format like "(Date, '')"
    duplicate_cols = [c for c in df.columns if c.startswith(f"({col},")]

    # Aggregate data by taking the first non-NaN value across duplicate columns
    if len(duplicate_cols) > 1:
        # Use np.where to prioritize non-null values across duplicates
        df[col] = df[duplicate_cols].bfill(axis=1).iloc[:, 0]
    
    # Drop duplicate columns except the main one
    df = df.drop(columns=[c for c in duplicate_cols if c != col])

# Display the resulting DataFrame with consolidated columns
print(df.head())
print(df)
