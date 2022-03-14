from Connect import XTSConnect
import pymongo
import json
import pytz
import requests
import pandas as pd
import numpy as np
import io
import math
from time import sleep
from datetime import date, datetime, timedelta, time
import configparser

def xts_data_token(API_KEY = 'cf5b8e617ac6ec78046852', API_SECRET = 'Osad425$Us',text = 'token'):
    XTS_API_BASE_URL = "https://xts.compositedge.com"
    source = "WEBAPI"
    xt = XTSConnect(API_KEY, API_SECRET, source= source)
    response = xt.marketdata_login()
    print(response)
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    token_filename = "data_{}.ini".format(text)
    print(token_filename )
    text_file = open(token_filename, "w")
    text_file.write("[datatoken] \n token=%s \n" % set_marketDataToken)
    text_file.write("[datauser] \n user=%s \n" % set_muserID)
    text_file.close()

def xts_order_token( API_KEY = 'f4599a642270f5031bd691', API_SECRET = 'Bxog870#vu', text = 'test'):
    XTS_API_BASE_URL = "https://xts.compositedge.com"
    source = "WEBAPI"
    xt = XTSConnect(API_KEY, API_SECRET, source= source)
    response = xt.interactive_login()
    print(response)
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    token_filename = "token_order_{}.ini".format(text)
    print(token_filename )
    text_file = open(token_filename, "w")
    text_file.write("[ordertoken] \n token=%s \n" % set_marketDataToken)
    text_file.write("[orderuser] \n user=%s \n" % set_muserID)
    text_file.close()

#xts_order_token("ad56ca1e5385d29696f579","Xyjh028$83",'test') # intraday nifty
#xts_order_token('f4599a642270f5031bd691', 'Eixv457$N2', 'banknifty')  # intraday bnf
#xts_data_token('6820acdf7865d76f3bc709','Qtsc817$fS','token1')
#xts_order_token("e3a64d975100976e6c3303", "Adoi655#hT", 'intraday') # nifty buy
#xts_order_token("a06fcbaadd347745187989", "Akjj644@YE", 'intraday') # nifty sell
#xts_order_token("ba5ca6389a9ac7af764211", "Kqgu816@tR", 'intraday') # bnf buy
#xts_order_token('760b867c3927939bdd2287', 'Yyvs027$5Y', 'intraday') # bnf sell


