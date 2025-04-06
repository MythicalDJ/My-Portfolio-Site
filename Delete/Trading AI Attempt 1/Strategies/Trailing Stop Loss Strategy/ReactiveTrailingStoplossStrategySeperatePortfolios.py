import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import config
import pybroker
import time
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig
from pybroker import Alpaca
import matplotlib.dates as mdates

API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY

pybroker.enable_data_source_cache('AlpacaCache')

##########################################################
#_______________________Settings_________________________#

StockOne = 'spy'
StockTwo = 'aapl'
StockThree = 'msft'
StockFour = 'amzn'
StockFive = 'tsla'
StockSix = 'goog'

DateFrom = '1/1/2018'
DateTo = '30/8/2024'
TimeFrame = '1d'

##########################################################

# Convert all stock symbols to uppercase
stocks = [StockOne.upper(), StockTwo.upper(), StockThree.upper(), StockFour.upper(), StockFive.upper(), StockSix.upper()]

# Create separate configurations and strategies for each stock
configs = {stock: StrategyConfig(initial_cash=1000) for stock in stocks}
strategies = {stock: Strategy(Alpaca(API_KEY, SECRET_KEY), DateFrom, DateTo, config=configs[stock]) for stock in stocks}

alpaca = Alpaca(API_KEY, SECRET_KEY)

def reactive_trailing_stop_loss_and_profit(ctx):
	if not hasattr(ctx, 'prev_win_rt'):
		ctx.prev_win_rt = 0

	if ctx.win_rate >= ctx.prev_win_rt:
		if ctx.symbol in [StockOne, StockThree, StockFive]:
			buy_with_trailing_stop_loss_and_profit(ctx)
		else:
			short_with_trailing_stop_loss_and_profit(ctx)
		ctx.prev_win_rt = ctx.win_rate
	else:
		if ctx.symbol in [StockOne, StockThree, StockFive]:
			short_with_trailing_stop_loss_and_profit(ctx)
		else:
			buy_with_trailing_stop_loss_and_profit(ctx)
		ctx.prev_win_rt = ctx.win_rate

def buy_with_trailing_stop_loss_and_profit(ctx):
	if not ctx.long_pos():
		ctx.buy_shares = ctx.calc_target_shares(1)
		ctx.stop_trailing_pct = 0.5

def short_with_trailing_stop_loss_and_profit(ctx):
	if not ctx.short_pos():
		ctx.sell_shares = ctx.calc_target_shares(1)
		ctx.stop_trailing_pct = 0.5

# Add execution for each strategy
for stock, strategy in strategies.items():
	strategy.add_execution(reactive_trailing_stop_loss_and_profit, [stock])

# Run backtest for each strategy
results = {stock: strategy.backtest(timeframe=TimeFrame, calc_bootstrap=True) for stock, strategy in strategies.items()}

# Combine trade data from all strategies
all_trades = pd.concat([pd.DataFrame(result.trades) for result in results.values()])
all_trades.to_excel('Excel_Files/ReactiveTrades.xlsx', index=False)

# Fetch and save historical price data for the stocks
price_data = {}
for stock in stocks:
	price_data[stock] = alpaca.query(stock, DateFrom, DateTo, TimeFrame)
	price_data[stock]['date'] = price_data[stock]['date'].dt.tz_localize(None)

with pd.ExcelWriter('Excel_Files/price_data.xlsx') as writer:
	for stock, data in price_data.items():
		data.to_excel(writer, sheet_name=f'{stock}_prices', index=False)

# Combine and save portfolio data
all_portfolios = pd.concat([result.portfolio for result in results.values()], axis=1)
all_portfolios.columns.symbol = stocks
all_portfolios.to_excel('Excel_Files/portfolio_data.xlsx', index=True)

def print_results(results, strategy_name):
	print(f"\n{strategy_name} Strategy Results")
	
	# Combine metrics from all strategies
	all_metrics = pd.concat([result.metrics_df for result in results.values()], axis=1)
	all_metrics.columns.symbol = stocks
	print("\nMetrics\n", all_metrics)

	# Plot portfolio market value over time for all strategies
	plt.figure(figsize=(10, 6))
	for stock, result in results.items():
		plt.plot(result.portfolio.index, result.portfolio['market_value'], label=stock)
	total_portfolio_value = sum(result.portfolio['market_value'] for result in results.values())
	plt.plot(results[next(iter(results))].portfolio.index, total_portfolio_value, label='Total Portfolio', color="purple")

	
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
	plt.gcf().autofmt_xdate()
	plt.xlabel('Date')
	plt.ylabel('Market Value')
	plt.title('Portfolio Market Value Over Time')
	plt.legend()
	plt.show()

	# Print trade information for all strategies
	all_trades = pd.concat([pd.DataFrame(result.trades) for result in results.values()])
	
	if not all_trades.empty:
		pd.set_option('display.max_rows', None)
		pd.set_option('display.max_columns', None)
		pd.set_option('display.width', None)
		pd.set_option('display.max_colwidth', None)

		def color_value(val):
			return f'\033[92m{val}\033[0m' if val > 0 else f'\033[91m{val}\033[0m'

		all_trades['pnl'] = all_trades['pnl'].apply(color_value)
		all_trades['return_pct'] = all_trades['return_pct'].apply(color_value)

		print("\nTrades:")
		print(tabulate(all_trades, headers='keys', tablefmt='psql'))
	else:
		print("\nNo trades for this strategy")

# Call the function with the results
print_results(results, "Reactive")