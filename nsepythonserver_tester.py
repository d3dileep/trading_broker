from nsepythonserver import *


def nse_quote_ltp(symbol):
  payload = nse_quote(symbol)
  print(payload.keys())
  all_dict = dict()

  selected_key = next((key for key in payload["expiryDatesByInstrument"] if "futures" in key.lower()), None)
  all_dict["fut_latest_expiry"]= payload["expiryDatesByInstrument"][selected_key][0]
  all_dict["fut_next_expiry"]= payload["expiryDatesByInstrument"][selected_key][1]
  selected_key = next((key for key in payload["expiryDatesByInstrument"] if "options" in key.lower()), None)
  all_dict["option_latest_expiry"]= payload["expiryDatesByInstrument"][selected_key][0]
  all_dict["option_next_expiry"]= payload["expiryDatesByInstrument"][selected_key][1]
  all_dict["current_price"] = payload["underlyingValue"]

  return payload, all_dict

symbol="BANKNIFTY"
payload, all_dict = nse_quote_ltp(symbol)
print(all_dict)
