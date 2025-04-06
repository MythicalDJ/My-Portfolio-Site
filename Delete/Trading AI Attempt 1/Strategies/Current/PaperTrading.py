import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI/First Attempt')
import alpaca
import os
import config
import TSPT as TSPT
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import date, datetime, timedelta

#Setup
API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
#if its before 7 am make the set the current date to be yesterday
if datetime.now().hour < 7:
	current_date = (date.today() - timedelta(1)).strftime('%Y-%m-%d')
else:
	current_date = datetime.now().strftime('%Y-%m-%d')

account = trading_client.get_account()

class TimeData:
	def __init__(self, DateFrom, DateTo, TimeFrame):
		self.DateFrom = DateFrom
		self.DateTo = DateTo
		self.TimeFrame = TimeFrame

# Define the stocks you want to trade
stocks = [
    TSPT.Stock('spy', 'Long', 0.25),
	]

# Define the time data
time_data = TimeData('2024-01-01', '2024-08-30', '2h')

test = TSPT.TrailingStopLossPaperTrading()
test.Set_stocks_to_test(stocks, time_data)
test.Set_Execs()
BTR = test.Backtest()
test.Write_trades_to_excel()
test.Print_results(BTR)