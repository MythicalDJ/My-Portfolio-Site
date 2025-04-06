import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import alpaca
import os
import config
import TSPT as TSPT
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import date, datetime, timedelta
from trade_info import TradeInfo

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
trade_info = TradeInfo()

class TimeData:
	def __init__(self, DateFrom, DateTo, TimeFrame):
		self.DateFrom = DateFrom
		self.DateTo = DateTo
		self.TimeFrame = TimeFrame

'''#Prepping a Market order 
aapl_asset = trading_client.get_asset('AAPL')
market_order_data = MarketOrderRequest(
	symbol='AAPL',
	qty=1,
	side=OrderSide.BUY,
	time_in_force=TimeInForce.GTC
)
# Making a market order
market_order = trading_client.submit_order(
	order_data=market_order_data
)

# Prepping a limit order
spy_asset = trading_client.get_asset('SPY')
limit_order_data = LimitOrderRequest(
	symbol = 'SPY',
	limit_price = 600,
	qty = 1,
	side = OrderSide.BUY,
	time_in_force = TimeInForce.DAY,
)

# Making a limit order
limit_order = trading_client.submit_order(
	order_data = limit_order_data
)'''

# Define the stocks you want to trade
stocks = [
	TSPT.Stock('spy', 'Long', 0.25),
	TSPT.Stock('AAPL', 'Long', 0.25),
	TSPT.Stock('msft', 'Long', 5),
]

first_run_date = trade_info.get_first_run_date()
time_data = TimeData(first_run_date, current_date, '2h')

test = TSPT.TrailingStopLossPaperTrading()
test.Set_stocks_to_test(stocks, time_data)
test.Set_Execs()
BTR = test.Backtest()

current_trades = test.get_current_trades()
stop_prices = test.get_stop_prices()

# Get existing positions from TradeInfo
existing_positions = trade_info.get_positions()

# Now you can use this information to place orders with Alpaca
for symbol, trade_info in current_trades.items():
	if symbol not in existing_positions:
		# Place a market buy order
		market_order_data = MarketOrderRequest(
			symbol=symbol,
			qty=trade_info['shares'],
			side=OrderSide.BUY,
			time_in_force=TimeInForce.GTC
		)
		market_order = trading_client.submit_order(order_data=market_order_data)
		
		# Place a stop loss order
		stop_price = stop_prices.get(symbol)
		if stop_price:
			stop_order_data = StopOrderRequest(
				symbol=symbol,
				qty=trade_info['shares'],
				side=OrderSide.SELL,
				time_in_force=TimeInForce.GTC,
				stop_price=stop_price
			)
			stop_order = trading_client.submit_order(order_data=stop_order_data)

test.Write_trades_to_excel()
test.Print_results(BTR)