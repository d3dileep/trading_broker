from Connect2 import XTSConnect
# import pymongo
import json
import pytz
import requests
import pandas as pd
import numpy as np
import io
import os
import math
from datetime import datetime, timedelta, time
import warnings
warnings.filterwarnings("ignore")

class XTS_parse:
    def __init__(self, token, userID, isInvestorClient):
        self.XTS_API_BASE_URL = "https://xts.compositedge.com"
        self.source = "WEBAPI"

        self.xt = XTSConnect(source=self.source, token=token, userID=userID, isInvestorClient=isInvestorClient)
        
        self.response = self.xt.get_config()
        # self.eq_data = self.equity_details()

    def get_id(self,item):
        if item=='NIFTY':
            self.quantity = 50
        if item=='BANKNIFTY':
            self.quantity = 25      
        self.data = pd.DataFrame(self.xt.search_by_scriptname(searchString=item)['result'])[['ExchangeSegment', 'ExchangeInstrumentID','Description']]
        
        return self.quantity,self.data
    def equity_details(self):
        df = pd.read_csv("https://public.fyers.in/sym_details/NSE_CM.csv")
        df.columns = [str(i) for i in range(df.shape[1])]
        df = df[["1","3","9","12","13"]]
        df.columns = ["Name","ExchangeSegment","Description", "ExchangeInstrumentID", "symbol"]
        df_new = df[df["Description"].str.contains("EQ")]
        return df_new
    def get_latest_price(self,item):
        id1 = self.data.loc[self.data['Description'] == item, ['ExchangeSegment','ExchangeInstrumentID']].iloc[0,1]
        instruments = [{'exchangeSegment': 2, 'exchangeInstrumentID': int(id1)}]
        jsoned = json.loads(self.xt.get_quote(Instruments=instruments,xtsMessageCode=1502,  publishFormat='JSON')['result']['listQuotes'][0])
        #print(jsoned)
        dt =float(jsoned['Touchline']['LastTradedPrice'])
        return dt

    def get_quote_oi(self, id, segemnt):
        """Get Quote Request"""
        # id1 = self.data.loc[self.data['Description'] == item, ['ExchangeSegment','ExchangeInstrumentID']].iloc[0,1]
        instruments = [{'exchangeSegment': segemnt, 'exchangeInstrumentID': int(id)}]
        response = self.xt.get_quote( Instruments=instruments, xtsMessageCode=1510, publishFormat='JSON')
        return int(json.loads(response['result']['listQuotes'][0])['OpenInterest'])
    

    def ExchangeInstrumentID(self):
            # Function to extract middle value
        df_index = pd.DataFrame({"Index":self.xt.get_index_list( exchangeSegment = 1)["result"]["indexList"]})
        df_index[['NAME OF COMPANY', 'EXCHANGEID']] = df_index['Index'].str.split('_', expand=True)
        # Function to extract expiry date and strike price from option name
        def extract_expiry_and_strike(option_name):
            parts = option_name.split()
            expiry_date = ' '.join(parts[1:4])
            strike_price = float(parts[-2])
            return expiry_date, strike_price

        def split_stock(row):
            if '-' in row['NAME OF COMPANY']:
                return pd.Series(row['NAME OF COMPANY'].split('-', 1))  # Split at the first occurrence of '-'
            else:
                return pd.Series([row['NAME OF COMPANY'], None])  # If no '-', return original value and None

        # Define URLs for CSV files
        url_option = "https://public.fyers.in/sym_details/NSE_FO.csv"
        url_equity = "https://public.fyers.in/sym_details/NSE_CM.csv"
        
        # Determine today's date for file naming and comparison
        today_date = datetime.now().date()
        
        # Define file paths
        option_csv_path = f"NSE_FO_{today_date}.csv"
        equity_csv_path = f"NSE_CM_{today_date}.csv"

        previous_date = today_date - timedelta(days=1)
        option_csv_previous = f"NSE_FO_{previous_date}.csv"
        equity_csv_previous = f"NSE_CM_{previous_date}.csv"
        
        # Check if files for today exist, otherwise download and save them
        if not os.path.exists(option_csv_path):
            df_op = pd.read_csv(url_option, header=None)[[1,9,12,15]].dropna()
            # print(df_op.iloc[1,:])
            df_op.columns = ["NAME OF OPTION","DESCRIPTION" ,"EXCHANGEID","ATM" ]
            df_op = df_op[~(df_op['NAME OF OPTION'].str.contains("FUT"))]
            # Apply the function to extract expiry dates and strike prices
            df_op['EXPIRY'], df_op['STRIKE'] = zip(*df_op['NAME OF OPTION'].apply(extract_expiry_and_strike))
            df_op.sort_values(by="EXCHANGEID", inplace=True)
            df_op.to_csv(option_csv_path, index=False)
        else:
            df_op = pd.read_csv(option_csv_path)
        
        if not os.path.exists(equity_csv_path):
            df_eq_fyer = pd.read_csv(url_equity, header=None)[[5,9,12,13]].dropna()
            df_eq_fyer.columns = ["ISIN NUMBER", "NAME OF COMPANY", "EXCHANGEID", "SYMBOL" ]
            # Apply the function to each row
            df_eq_fyer[['NAME OF COMPANY', 'SERIES']] = df_eq_fyer.apply(split_stock, axis=1)
            df_eq_fyer.sort_values(by="EXCHANGEID", inplace=True)
            df_eq_fyer.to_csv(equity_csv_path, index=False)
            # Delete previous day's CSV files if they exist
            if os.path.exists(option_csv_previous):
                os.remove(option_csv_previous)
            if os.path.exists(equity_csv_previous):
                os.remove(equity_csv_previous)
        else:
            df_eq_fyer = pd.read_csv(equity_csv_path)

        return df_op, df_index, df_eq_fyer
        
    def read_data(self, symbol_id, interval, exchange,division='NIFTY', days=5, prime=False):
        tzinfo = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz= tzinfo)#tz= tzinf
        today = now.date()
        current_time = time(now.hour, now.minute, now.second)

        to_d = datetime.combine(today, current_time)

        # if prime:
        from_d = datetime.combine(today -timedelta(days=days), time(9,15,00) )
        # if days:
        #     # from_d = datetime.combine(days, time(9,15,00) )

        from_d = from_d.strftime("%b %d %Y %H%M%S")
        to_d = to_d.strftime("%b %d %Y %H%M%S")

        try:
            response = self.xt.get_ohlc(exchangeSegment=exchange,exchangeInstrumentID=symbol_id,
                startTime=from_d,endTime=to_d,compressionValue=interval)
            # print(response)
            data = response['result']['dataReponse']
            result = [x.strip() for x in data.split(',')]
            value =[]
            for item in result:
              data = [x.strip() for x in item.split('|')]
              value.append(data)
            data = pd.DataFrame(value,columns=['date','open','high','low','close','volume','oi','red'])[['date','open','high','low','close','volume','oi']]
            data['date'] = pd.to_datetime(data['date'], unit="s")
            
            
            data[['open','high','low','close','volume','oi']] = data[['open','high','low','close','volume','oi']].apply(pd.to_numeric)

        except Exception as e:
            print(item, e)
            pass
        return data, to_d

    def get_instr_list(self):
        nsefo_instr_url = 'http://public.fyers.in/sym_details/NSE_FO.csv'
        s=requests.get(nsefo_instr_url).content
        fo_instr=pd.read_csv(io.StringIO(s.decode('utf-8')), header=None)
        fo_instr[1] = fo_instr[1].apply(lambda x: x.upper())

        return fo_instr

    def get_options_contract(self, underlying, opt_type, strike, nearest_expiry, monthend_expiry):

        if monthend_expiry == 'YES':
            fyers_symbol = 'NSE:' + underlying + str(nearest_expiry.year - 2000) + nearest_expiry.strftime('%b').upper() + str(strike)
        else:
            fyers_symbol = 'NSE:' + underlying + str(nearest_expiry.year - 2000) + str(int(nearest_expiry.strftime('%m'))) + nearest_expiry.strftime('%d') + str(strike)
        td_symbol = underlying + str(nearest_expiry.year - 2000) + nearest_expiry.strftime('%m') + nearest_expiry.strftime('%d') + str(strike)

        if opt_type == 'CE':
            fyers_symbol = fyers_symbol + 'CE'
            td_symbol = td_symbol + 'CE'
        else:
            fyers_symbol = fyers_symbol + 'PE'
            td_symbol = td_symbol + 'PE'

        return fyers_symbol.replace("NSE:",''), td_symbol

    def roundup(self,x,y):
        return int(math.ceil(x / y)) * y
    def rounddown(self,x,y):
        return int(math.floor(x / y)) * y
    def roundoff(self,x):
        return round(x,2)

class XTS_order:
  def __init__(self, token, userID, isInvestorClient):
    self.XTS_API_BASE_URL = "https://xts.compositedge.com"
    self.source = "WEBAPI"

    self.xt = XTSConnect(self.source, token=token, userID=userID, isInvestorClient=isInvestorClient)
    
  def place_order(self, data, quantity, item, action, q_multiplier):
    id1 = int(data.loc[data['Description'] == item, ['ExchangeSegment','ExchangeInstrumentID']].iloc[0,1])
    order = self.xt.place_order(exchangeSegment='NSEFO', exchangeInstrumentID=id1, productType='NRML', orderType='MARKET',
            orderSide=action, timeInForce=self.xt.VALIDITY_DAY, orderQuantity= quantity * q_multiplier, orderUniqueIdentifier="454845", disclosedQuantity=0, limitPrice=0, stopPrice=0)
    print('place order response', order)

  def exit_order(self, data, quantity, item, q_multiplier):
    id1 = int(data.loc[data['Description'] == item, ['ExchangeSegment','ExchangeInstrumentID']].iloc[0,1])
    exit = self.xt.squareoff_position(exchangeSegment='NSEFO', exchangeInstrumentID=id1, productType='NRML',squareoffMode='Netwise', positionSquareOffQuantityType='ExactQty', squareOffQtyValue=quantity * q_multiplier,blockOrderSending=True, cancelOrders=True)
    print('exit order response',exit)

  def get_positions(self):
    resp = self.xt.get_position_netwise()
    return resp

  def get_balance(self):
    """Get Balance API call grouped under this category information related to limits on equities, derivative,
    upfront margin, available exposure and other RMS related balances available to the user."""
    if self.xt.isInvestorClient:
      try:
        params = {}
        if not self.xt.isInvestorClient:
            params['clientID'] = self.xt.userID
        response = self.xt._get('user.balance', params)
        return response
      except Exception as e:
        return response['description']
    else:
      print("Balance : Balance API available for retail API users only, dealers can watch the same on dealer "
              "terminal")
  
  
  def get_holding(self):
    """Holdings API call enable users to check their long term holdings with the broker."""
    try:
      params = {}
      if not self.xt.isInvestorClient:
        params['clientID'] = self.xt.userID

      response = self.xt._get('portfolio.holdings', params)
      return response
    except Exception as e:
      return response['description']            
                  
