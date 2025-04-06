import pybroker
from pybroker import Alpaca, StrategyConfig, Strategy, ExecContext
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Backend.Credentials import *
alpaca = Alpaca(ALPACA_API_KEY, ALPACA_API_SECRET_KEY)
alpaca.adjust = 'all'
pybroker.enable_data_source_cache('RaPS')


def buy_highest_volume(ctx: ExecContext):
	# If there are no long positions across all tickers being traded:
	if not tuple(ctx.long_positions()):
		ctx.buy_shares = ctx.calc_target_shares(1)
		ctx.hold_bars = 2
		ctx.score = ctx.volume[-1]
		

def buy_and_hold(ctx: ExecContext):
	if not ctx.long_pos() and ctx.bars >=100:
		ctx.buy_shares = 100
		ctx.hold_bars = 300

def pos_size_handler(ctx: ExecContext):
	#Fetch all buy signals
	signals = tuple(ctx.signals("buy"))
	#If there are no buy signals, return
	if not signals:
		return
	# Calculates the inverse volatility, where volatility is the standard deviation of the close prices for the last 100 days.
	get_inverse_volatility = lambda signal: 1/np.std(signal.bar_data.close[-100:])
	# Sums the inverse volatilities of all buy signals
	total_inverse_volatility = sum(map(get_inverse_volatility, signals))
	for signal in signals:
		size = get_inverse_volatility(signal) / total_inverse_volatility
		# Calculate the number of shares given the latest close price.
		shares = ctx.calc_target_shares(size, signal.bar_data.close[-1], cash=95_000)
		ctx.set_shares(signal, shares)


Strategy.set_pos_size_handler(pos_size_handler)

Strategy = Strategy(alpaca, '2022-01-01','2025-01-01')
Strategy.add_execution(buy_and_hold, ['SPY', 'AAPL' , "TSLA" , "MSFT"])
result = Strategy.backtest(timeframe="1d")
print(result.trades)


