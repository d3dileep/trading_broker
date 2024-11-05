from Connect_new import XTSConnect

import os
import sys

# Change to the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def xts_order_token( API_KEY = 'f4599a642270f5031bd691', API_SECRET = 'Bxog870#vu', text = 'test'):
    XTS_API_BASE_URL = "https://xts.compositedge.com"
    source = "WEBAPI"
    xt = XTSConnect(API_KEY, API_SECRET, source= source)
    response = xt.interactive_login()
    print(response)
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    token_filename = "./token_order_{}.ini".format(text)
    print(token_filename )
    text_file = open(token_filename, "w")
    text_file.write("[ordertoken] \n token=%s \n" % set_marketDataToken)
    text_file.write("[orderuser] \n user=%s \n" % set_muserID)
    text_file.close()

def xts_data_token(API_KEY , API_SECRET ,text = 'token'):
    XTS_API_BASE_URL = "https://xts.compositedge.com"
    source = "WEBAPI"
    xt = XTSConnect(API_KEY, API_SECRET, source= source)
    response = xt.marketdata_login()
    print("API connection response:", response)
    set_marketDataToken = response['result']['token']
    set_muserID = response['result']['userID']
    token_filename = "./data_{}.ini".format(text)
    print(token_filename )
    text_file = open(token_filename, "w")
    text_file.write("[datatoken] \n token=%s \n" % set_marketDataToken)
    text_file.write("[datauser] \n user=%s \n" % set_muserID)
    text_file.close()



# xts_data_token('1d6c9410fdb291b0a1d933','Toqb450@EN')
# xts_data_token("85135d5e950fbc8b29d999","Vqhv461@eP")


