from download_ohlc_xts import get_dat_xts
import datetime
import pytz
IST = pytz.timezone('Asia/Kolkata')
current_time = datetime.datetime.now(IST).time()
print(current_time)
get_dat_xts('BANKNIFTY', 2)
