from pybroker import Alpaca, StrategyConfig, Strategy
import pybroker
from pybroker.context import ExecContext
import os
import sys
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Backend.Credentials import *
from Backend.InfoAndGraphs import Graphs
alpaca = Alpaca(ALPACA_API_KEY, ALPACA_API_SECRET_KEY)
alpaca.adjust = 'all'

config = StrategyConfig(initial_cash=10000)
strategy = Strategy(alpaca, '2022-01-03','2024-01-10' , config)

def buy_low(ctx: ExecContext):
	#If already in a position, do nothing:
	if ctx.long_pos():
		return
	#If the latest close price is less than the previous day's low price,
	#then place a buy order:
	if ctx.bars >= 2 and ctx.close[-1] < ctx.low[-2]:
		#Buy a number of shares that is equal to 25% of the portfolio:
		ctx.buy_shares = ctx.calc_target_shares(0.2)
		ctx.stop_loss_pct = 5
		ctx.stop_trailing_pct = 7

def short_high(ctx: ExecContext):
	# If shares were already shorted then return.
	if ctx.short_pos():
		return
	# If the latest close price is more than the previous day's high price,
	# then place a sell order.
	if ctx.bars >= 2 and ctx.close[-1] > ctx.high[-2]:
		ctx.sell_shares = ctx.calc_target_shares(0.25)
	   
		# Cover the shares after 2 bars (in this case, 2 days).
		ctx.hold_bars = 2


strategy.add_execution(buy_low, 'SPY')
#strategy.add_execution(short_high, 'TSLA')
strategy.add_execution(buy_low, 'AAPL')


result = strategy.backtest(timeframe='1d', calc_bootstrap=True)

Graphs().plot_market_value(result)
Graphs().plot_normalized_returns(result)
Graphs().DisplayAsTable(result)
