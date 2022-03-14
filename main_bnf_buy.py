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
from token1 import xts_data_token, xts_order_token
from xts_class2 import XTS_parse, XTS_order
from strategy import strike_bnf_buy
import configparser

def main(item):
    myclient = pymongo.MongoClient("mongodb+srv://chatteltech19:chattel19@cluster0-icted.mongodb.net/test?authSource=admin&replicaSet=Cluster0-shard-0&readPreference=primary&appname=MongoDB%20Compass&ssl=true")
    mydb = myclient["algo"]
    
    cfg = configparser.ConfigParser()
    xts_data_token("e7f57c31e7a4dd7a2d3610", "Yryw010@@Q",'bnf_buy')
    cfg.read("data_{}.ini".format('bnf_buy'))
    xts= XTS_parse(token=cfg.get('datatoken', 'token'), userID=cfg.get('datauser', 'user'), isInvestorClient=True)
    xts_order_token("ba5ca6389a9ac7af764211", "Kqgu816@tR", 'bnf_buy')
    cfg.read('token_order_{}.ini'.format('bnf_buy'))    
    xts_o = XTS_order(token=cfg.get('ordertoken', 'token'), userID=cfg.get('orderuser', 'user'), isInvestorClient=True)
    quantity, dt = xts.get_id(item)

    exchange = "NSEFO"
    tzinfo = pytz.timezone('Asia/Kolkata')    
    underlying_mapping = {'NIFTY 50': 'NIFTY', 'NIFTY BANK': 'BANKNIFTY'}

    tradable_sell = []
    tradable_buy = []
    traded = []
    strikes = []
    lot = 1
    fo_instr_list = xts.get_instr_list()
    all_expiries = sorted(list(set([datetime.strptime(str(x)[4:10], '%y%m%d') for x in fo_instr_list[0].tolist()])))
    ## fetch nearest expiry if its friday, monday, or tuesday else next expiry
    if datetime.now(tz= tzinfo).weekday() in [0,1,4,5,6]:
        nearest_expiry = all_expiries[0]
    elif datetime.now(tz= tzinfo).weekday() in [2,3]:
        del all_expiries[0]
        nearest_expiry = all_expiries[0]

    #nearest_expiry = all_expiries[0]
    monthend_expiry = 'YES' if len([x for x in all_expiries if x.year == nearest_expiry.year and x.month == nearest_expiry.month]) == 1 else 'NO'
    print('starting calculation')
    quantity,data=xts.get_id(item)
    response=xts_o.get_positions()
    print('get balance response',response)
    print('get holding response',xts_o.get_holding())
    try:
        data1 =list(mydb["enter_trade"].find({},{"_id": 0,"time": 0}))
        if data1:
            for ele in data1:
              if ele['category'] == item and ele['action'] == 'bought':
                traded.append(ele)
                strikes.append(ele['symbol'])
        print('traded',traded)
    except Exception as e:
        print(e)
        pass


    while datetime.now(tz= tzinfo).time() < time(15, 30, 0):
        try:
            now = datetime.now(tz= tzinfo)
            
            if datetime.now(tz= tzinfo).time() >= time(9, 15, 0):
                df, now = xts.read_data(item, 900,"NSECM", prime=True)
                day_delta = df['date'][-48:-47].dt.date.values[0]
                if len(traded)==0:
                    if abs(df["open"][-1:].values[0] - df["close"][-2:-1].values[0]) >0.0039*df["close"][-2:-1].values[0] and datetime.now(tz= tzinfo).time() < time(9, 30, 0):
                        print("Gap Opening, sleeping till 09:30")
                        sleep((datetime(datetime.now(tz= tzinfo).year,datetime.now(tz= tzinfo).month,datetime.now(tz= tzinfo).day,9, 30) - datetime.now(tz= tzinfo).replace(tzinfo=None)).total_seconds())
                        tradable_buy.extend( strike_bnf_buy(item,nearest_expiry,monthend_expiry,exchange, xts, day_delta))
                    else:
                        tradable_buy.extend( strike_bnf_buy(item,nearest_expiry,monthend_expiry,exchange, xts, day_delta))
                    print(now,"\n","SELL",tradable_sell,"\n","BUY",tradable_buy)
                    try:
                        mydb["list_buy_{}".format(item)].delete_many({})
                        mydb["list_buy_{}".format(item)].insert_many(tradable_buy)
                    except:
                        pass
                if tradable_buy and datetime.now(tz= tzinfo).time() >= time(9, 25, 0):
                  for spot in tradable_buy :
                    if spot not in strikes and len(strikes) < 1:
                        sleep(1)
                        close_price = xts.get_latest_price(spot["symbol"])
                        mydb["list_buy_{}".format(item)].find_one_and_update({'symbol':spot["symbol"]},{'$set': {'current_p':close_price}})
                        if datetime.now(tz= tzinfo).second == 0:
                            print(datetime.now(tz= tzinfo).time(), spot["symbol"], close_price)
                        if close_price >= spot["entry_p"] :
                            print({"symbol":spot["symbol"], "entry_p":close_price, "action":"bought","target":spot["target"],"stoploss":spot["stoploss"],"lot":lot})
                            xts_o.place_order(data,quantity,spot["symbol"],'BUY',lot)
                            mydb["enter_trade"].insert_one({"time": now,'category':item, "symbol":spot["symbol"], "entry_p":close_price, "action":"bought","target":spot["target"],"stoploss":spot["stoploss"],"lot":lot})
                            traded.append({"time": now,"symbol":spot["symbol"], "entry_p":close_price, "action":"bought","target":spot["target"],"stoploss":spot["stoploss"],"lot":lot})
                            strikes.append(spot['symbol'])
                # exit the entered positions
                if traded:
                    for position in traded:
                        sleep(1)
                        close_price = xts.get_latest_price(position["symbol"])
                        if datetime.now(tz= tzinfo).second in range(3):
                            print(datetime.now(tz= tzinfo).time(), position["symbol"], close_price)
                        try:
                            mydb["list_buy_{}".format(item)].find_one_and_update({'symbol':position["symbol"]},{'$set': {'current_p':close_price}})
                        except:
                            pass

                        if  position["action"] == "bought" and position["target"] <= close_price and position["symbol"] in strikes:
                            print(position["symbol"], close_price, "exit bought")
                            xts_o.exit_order(data,quantity,position["symbol"],1)
                            position["lot"] -=1
                            position["target"] = xts.roundoff(1.2 *position["target"])
                            position["stoploss"] = xts.roundoff(0.8 *position["target"])
                            mydb["enter_trade"].find_one_and_update({'symbol':position["symbol"]},{'$set': {'target': position["target"], 'stoploss':position["stoploss"]}})
                            mydb["exit_trade"].insert_one({"time": now,"symbol":position["symbol"], "exit_p":close_price, "action":" exit bought", "target": position["target"], "stoploss":position["stoploss"], "lot":1,"PnL": xts.roundoff(close_price - position["entry_p"])})
                            if position["lot"]==0:
                                traded.remove(position)
                                strikes.remove(position["symbol"])
                                mydb["enter_trade"].find_one_and_delete({"symbol":position["symbol"]})
                                # updates the entry, target, and stop loss after sell
                                tradable_sell = []
                                tradable_buy = []
              
                                tradable_buy.extend( strike_bnf_buy(item,nearest_expiry,monthend_expiry,exchange, xts, day_delta))
                                mydb["list_buy_{}".format(item)].delete_many({})
                                mydb["list_buy_{}".format(item)].insert_many(tradable_buy)
                                print(now,"\n","BUY",tradable_buy) 

                        if datetime.now(tz= tzinfo).weekday() == 3 and position["time"].weekday() in [0,1,4] and datetime.now(tz= tzinfo).time() >= time(15, 0, 0):                            
                            print(position["symbol"], close_price, "stoploss bought")
                            xts_o.exit_order(data,quantity,position["symbol"],position["lot"])
                            position["lot"] = 0
                            mydb["exit_trade"].insert_one({"time": now,"symbol":position["symbol"], "exit_p":close_price, "action":" stoploss bought", "target": position["target"], "stoploss":position["stoploss"], "lot":position["lot"],"PnL": xts.roundoff(close_price - position["entry_p"])})
                            if position["lot"]==0:
                                traded.remove(position)
                                strikes.remove(position["symbol"]) 
                                mydb["enter_trade"].find_one_and_delete({"symbol":position["symbol"]})
                                # updates the entry, target, and stop loss after sell
                                tradable_sell = []
                                tradable_buy = []
                               
                                tradable_buy.extend( strike_bnf_buy(item,nearest_expiry,monthend_expiry,exchange, xts, day_delta))
                                mydb["list_buy_{}".format(item)].delete_many({})
                                mydb["list_buy_{}".format(item)].insert_many(tradable_buy)
                                print(now,"\n","BUY",tradable_buy) 

                        if position["action"] == "bought" and position["stoploss"] >= close_price and position["symbol"] in strikes:
                            print(position["symbol"], close_price, "stoploss bought")
                            xts_o.exit_order(data,quantity,position["symbol"],position["lot"])
                            position["lot"] = 0
                            mydb["exit_trade"].insert_one({"time": now,"symbol":position["symbol"], "exit_p":close_price, "action":" stoploss bought", "target": position["target"], "stoploss":position["stoploss"], "lot":position["lot"],"PnL": xts.roundoff(close_price - position["entry_p"])})
                            if position["lot"]==0:
                                traded.remove(position)
                                strikes.remove(position["symbol"]) 
                                mydb["enter_trade"].find_one_and_delete({"symbol":position["symbol"]})
                                # updates the entry, target, and stop loss after sell
                                tradable_sell = []
                                tradable_buy = []
                               
                                tradable_buy.extend( strike_bnf_buy(item,nearest_expiry,monthend_expiry,exchange, xts, day_delta))
                                mydb["list_buy_{}".format(item)].delete_many({})
                                mydb["list_buy_{}".format(item)].insert_many(tradable_buy)
                                print(now,"\n","BUY",tradable_buy) 
    
        except Exception as e:
          print(e)
if __name__ == "__main__":   
    main('BANKNIFTY')
