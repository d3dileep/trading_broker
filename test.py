import pandas as pd
df = pd.read_csv("NSE_FO_2024-09-10.csv")
print(df.head())
df["SYMBOL"] = df["NAME OF OPTION"].str.split().str[0]
df_filter = df[df["SYMBOL"].str.contains("NIFTY")]
print(df_filter["SYMBOL"].unique(), df_filter.shape)
