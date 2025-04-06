from pybroker import Alpaca
import pybroker
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Backend.Credentials import *

alpaca = Alpaca(ALPACA_API_KEY, ALPACA_API_SECRET_KEY)
pybroker.enable_data_source_cache('datasources')

df = alpaca.query(["SPY"], start_date= "2025/01/01", end_date= "2025/01/02", timeframe="1m", adjust="all")

print(df)