import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import config
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np	
import pybroker
import decimal
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig, Alpaca
from datetime import datetime, timedelta

API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY

# Initialize Alpaca
alpaca = Alpaca(API_KEY, SECRET_KEY)
alpaca.adjust = 'all'
pybroker.enable_data_source_cache('AlpacaCache')


class Stock:
	def __init__(self, symbol, strategy, trailing_stop_loss_pct):
		self.symbol = symbol
		self.strategy = strategy
		self.trailing_stop_loss_pct = trailing_stop_loss_pct

class TrailingStopLossPaperTrading:
	def __init__(self):
		self.daytrades = 0
		self.trade_history = []
		self.last_update_date = None

	def update_daytrade_count(self, current_date):
		if not isinstance(current_date, pd.Timestamp):
			current_date = pd.Timestamp(current_date)

		# If it's a new day, recalculate day trades
		if self.last_update_date is None or current_date.date() != self.last_update_date.date():
			five_trading_days_ago = self.get_trading_day_offset(current_date, -5)
			
			# Keep only trades within the last 5 trading days
			self.trade_history = [
				(e_date, x_date) for e_date, x_date in self.trade_history
				if x_date is not None and x_date > five_trading_days_ago
			]
			
			# Recalculate day trades
			self.daytrades = sum(1 for e_date, x_date in self.trade_history if e_date.date() == x_date.date())
			
			self.last_update_date = current_date

		print(f"Current day trades: {self.daytrades}")  # Debug print

	def add_trade(self, entry_date, exit_date):
		if not isinstance(entry_date, pd.Timestamp):
			entry_date = pd.Timestamp(entry_date)
		if not isinstance(exit_date, pd.Timestamp):
			exit_date = pd.Timestamp(exit_date)

		self.trade_history.append((entry_date, exit_date))
		
		# If it's a day trade, increment the counter
		if entry_date.date() == exit_date.date():
			self.daytrades += 1
			print(f"Day trade added. Total: {self.daytrades}")  # Debug print

	def get_trading_day_offset(self, date, offset):
		# This is a simplified version. You might need to adjust it to account for holidays.
		current_date = date
		days_counted = 0
		while days_counted < abs(offset):
			current_date += timedelta(days=1 if offset > 0 else -1)
			if current_date.weekday() < 5:  # Monday = 0, Friday = 4
				days_counted += 1
		return current_date
	
	def can_day_trade(self, current_date):
		self.update_daytrade_count(current_date)
		return self.daytrades < 3  # Allow up to 3 day trades, make the 4th one restricted
	
	
	def Set_stocks_to_test(self, StockList, TimeData):
		self.stocks = StockList  # EG ['AAPL', 'MSFT', 'GOOGL']
		self.DateFrom = TimeData.DateFrom  # EG '2022-01-01'
		self.DateTo = TimeData.DateTo  # EG '2022-12-31'
		self.TimeFrame = TimeData.TimeFrame  # EG '1d'
		for stock in self.stocks:
			stock.symbol = stock.symbol.upper()

		# Create separate configurations and strategies for each stock
		self.configs = {stock: StrategyConfig(initial_cash=1000) for stock in self.stocks}
		self.strategies = {stock: Strategy(Alpaca(API_KEY, SECRET_KEY), self.DateFrom, self.DateTo, config=self.configs[stock], adjust='all') for stock in self.stocks}

	def Buy_with_trailing_stop_loss_and_profit(self, ctx):
		current_date = ctx._curr_date

		if self.can_day_trade(current_date):
			if ctx.long_pos():
				# Update stop loss based on trailing stop logic
				self.Calculate_Stop(ctx)

				# Check if the price opens below the stop
				if ctx.open[-1] < self.stop:
					# If the daily low is less than 2.5% of the open price
					if ctx.low[-1] < ctx.open[-1] * 0.975:
						# Sell at 2.5% of the open price
						sell_price = ctx.open[-1] * 0.975
						self.add_trade(ctx._portfolio.long_positions[ctx.symbol].entries[0].date, current_date)
						ctx._portfolio.sell(current_date, ctx.symbol, ctx._portfolio.long_positions[ctx.symbol].entries[0].shares, decimal.Decimal(str(sell_price)))
					
					# Else if the high is greater than the stop
					elif ctx.high[-1] >= self.stop:
						# And if the price closes above the stop
						if ctx.close[-1] > self.stop:
							# Continue the trailing stop
							return
						else:
							# Sell at the stop
							self.add_trade(ctx._portfolio.long_positions[ctx.symbol].entries[0].date, current_date)
							ctx._portfolio.sell(current_date, ctx.symbol, ctx._portfolio.long_positions[ctx.symbol].entries[0].shares, decimal.Decimal(str(self.stop)))
					else:
						'''Sell at the close price'''
						#Not executing any trades here seems to imporove profitability quite substantially, I am not entirely sure why but i will say that the algo is
						# 'forgiving' and that, for now, the code to sell at the close price should be commented out.
						#ctx._portfolio.sell(current_date, ctx.symbol, ctx._portfolio.long_positions[ctx.symbol].entries[0].shares, decimal.Decimal(str(ctx.close[-1])))
						#self.add_trade(ctx._portfolio.long_positions[ctx.symbol].entries[0].date, current_date)
			else:
				# Buy new shares
				self.shares_bought = ctx.calc_target_shares(1)
				ctx._portfolio.buy(current_date, ctx.symbol, self.shares_bought, decimal.Decimal(str(ctx.open[-1])))
				# We don't add to trade_history here because the trade hasn't been closed yet
		else:
			print(f"Day trade limit reached. Cannot open new positions on {current_date}")

	def Short_with_trailing_stop_loss_and_profit(self, ctx):
		if not ctx.short_pos():
			ctx.sell_shares = ctx.calc_target_shares(1)
			ctx.stop_trailing_pct = next(stock.trailing_stop_loss_pct for stock in self.stocks if stock.symbol == ctx.symbol)

	def Reactive_trailing_stop_loss_and_profit(self, ctx):
		if not hasattr(ctx, 'prev_win_rt'):
			ctx.prev_win_rt = 0
		for stock in self.stocks:
			if ctx.symbol == stock.symbol and stock.strategy == 'Reactive':
				if ctx.win_rate >= ctx.prev_win_rt:
					self.Buy_with_trailing_stop_loss_and_profit(ctx)
				else:
					self.Short_with_trailing_stop_loss_and_profit(ctx)
				ctx.prev_win_rt = ctx.win_rate

	def Calculate_Stop(self, ctx):
		if ctx.bars == 0:
			self.entry = ctx.open[-1]
			self.stop = self.entry * 0.975
		# Calculate stop price
		else:
			for stock in self.stocks:
				self.entry = ctx.open[-2]
				self.amount = self.entry * self.stop_pct / 100
				self.stop = ctx.high[-2] - self.amount

	def Set_Execs(self):
		# Clear previous executions and add new ones
		for stock, strategy in self.strategies.items():
			strategy.clear_executions()
			self.stop_pct = next(stock.trailing_stop_loss_pct for stock in self.stocks if stock.symbol == stock.symbol)
			if stock.strategy == 'Long':
				strategy.add_execution(self.Buy_with_trailing_stop_loss_and_profit, stock.symbol)
			elif stock.strategy == 'Short':
				strategy.add_execution(self.Short_with_trailing_stop_loss_and_profit, stock.symbol)
			elif stock.strategy == 'Reactive':
				strategy.add_execution(self.Reactive_trailing_stop_loss_and_profit, stock.symbol)

	def Backtest(self):
		self.Set_Execs()
		# Run backtest for each strategy
		global results
		results = {stock: strategy.backtest(timeframe=self.TimeFrame, calc_bootstrap=True) for stock, strategy in self.strategies.items()}
		return results

	def Fetch_PD(self):
		# Fetch and save historical price data for the stocks
		global price_data
		price_data = {}
		for stock in self.stocks:
			price_data[stock] = alpaca.query(stock.symbol, self.DateFrom, self.DateTo, self.TimeFrame, adjust='all')
			price_data[stock]['date'] = price_data[stock]['date'].dt.tz_localize(None)

	def Write_trades_to_excel(self):
		# Combine trade data from all strategies and move the file to the 'Excel Files' folder
		all_trades = pd.concat([pd.DataFrame(result.trades) for result in results.values()])
		all_trades.to_excel('Excel_Files/TrailingStopLossStrategy - Multiple Stocks.xlsx', index=False)

		self.Fetch_PD()

		with pd.ExcelWriter('Excel_Files/price_data.xlsx') as writer:
			for stock, data in price_data.items():
				data.to_excel(writer, sheet_name=f'{stock.symbol}_prices', index=False)

		# Combine and save portfolio data
		all_portfolios = pd.concat([result.portfolio for result in results.values()], axis=1)
		all_portfolios.columns.symbol = self.stocks
		all_portfolios.to_excel('Excel_Files/portfolio_data.xlsx', index=True)

	def Print_results(self, results):
		print("Strategy Results")
		
		# Combine metrics from all strategies
		all_metrics = pd.concat([result.metrics_df for result in results.values()], axis=1)
		all_metrics.columns.symbol = [stock.symbol for stock in self.stocks]
		print("\nMetrics\n", all_metrics)

		#If price data has not been fetched, fetch it
		try:
			price_data
		except NameError:
			self.Fetch_PD()

		# Plot price data for all stocks in a separate window
		plt.figure(figsize=(12, 6))
		for stock, data in price_data.items():
			plt.plot(data['date'], data['close'], label=f"{stock.symbol} Close Price")

		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
		plt.gcf().autofmt_xdate()
		plt.xlabel('Date')
		plt.ylabel('Price')
		plt.title('Stock Prices Over Time')
		plt.legend()

		# Plot portfolio market value over time for all strategies
		plt.figure(figsize=(10, 6))
		for stock, result in results.items():
			plt.plot(result.portfolio.index, result.portfolio['market_value'], label=stock.symbol)
		total_portfolio_value = sum(result.portfolio['market_value'] for result in results.values())
		plt.plot(next(iter(results.values())).portfolio.index, total_portfolio_value, label='Total Portfolio', color="purple")

		plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
		plt.gcf().autofmt_xdate()
		plt.xlabel('Date')
		plt.ylabel('Market Value')
		plt.title('Portfolio Market Value Over Time')
		plt.legend()


		# Display all plots
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
		
		print (self.count)