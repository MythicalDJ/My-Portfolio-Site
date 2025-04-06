from pybroker import Alpaca, StrategyConfig, Strategy
import pybroker
import os
import sys
import matplotlib.pyplot as plt
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from Backend.Credentials import *
alpaca = Alpaca(ALPACA_API_KEY, ALPACA_API_SECRET_KEY)
alpaca.adjust = 'all'

config = StrategyConfig(initial_cash=500_000)
strategy = Strategy(alpaca, '2022-01-01','2022-01-10' , config)

def buy_low(ctx):
	#If already in a position, do nothing:
	if ctx.long_pos():
		return
	#If the latest close price is less than the previous day's low price,
	#then place a buy order:
	if ctx.bars >= 2 and ctx.close[-1] < ctx.low[-2]:
		#Buy a number of shares that is equal to 25% of the portfolio:
		ctx.buy_shares = ctx.calc_target_shares(0.25)
		#Set the limit price of the order:
		ctx.buy_limit_price = ctx.close[-1] - 0.01
		#Hold the position for 3 bars before liquidating (in this case, 3 days):
		ctx.hold_bars = 3

def short_high(ctx):
	# If shares were already shorted then return.
    if ctx.short_pos():
        return
    # If the latest close price is more than the previous day's high price,
    # then place a sell order.
    if ctx.bars >= 2 and ctx.close[-1] > ctx.high[-2]:
        # Short 100 shares.
        ctx.sell_shares = 100
        # Cover the shares after 2 bars (in this case, 2 days).
        ctx.hold_bars = 2


strategy.add_execution(buy_low, 'SPY')
strategy.add_execution(short_high, 'TSLA')

result = strategy.backtest(timeframe='1d')
chart = plt.subplot2grid((3, 2), (0, 0), rowspan=3, colspan=2)
chart.plot(result.portfolio.index, result.portfolio['market_value'])
plt.show()
print(result.positions)