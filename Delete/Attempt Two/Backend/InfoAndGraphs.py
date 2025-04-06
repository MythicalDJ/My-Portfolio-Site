from tabulate import tabulate
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# This is a script that will be used to generate the graphs for the result of the backtest. It will be called in my main script

class Graphs():

	def __init__(self):
		pass


	def plot_market_value(self, results):
		"""
		Plots the market value of the portfolio over time for each symbol,
		as well as the overall portfolio market value.
		"""
		positions_df = results.positions
		unique_symbols = positions_df.index.get_level_values(0).unique()

		for symbol in unique_symbols:
			symbol_data = positions_df.xs(symbol, level=0)
			plt.plot(
				symbol_data.index,
				symbol_data['market_value'],
				label=f'{symbol} Market Value'
			)

		plt.plot(
			results.portfolio.index,
			results.portfolio['market_value'],
			label='Portfolio Market Value'
		)

		plt.xlabel('Date')
		plt.ylabel('Market Value')
		plt.title('Portfolio Market Value Over Time')
		plt.legend()
		plt.show()


	def DisplayAsTable(self, results):
		"""
		Displays the trades in a formatted table with colored values for positive/negative numbers
		"""
		trades_df = pd.DataFrame(results.trades)
		if trades_df.empty:
			print("\nNo trades for this strategy")
			return

		def color_value(val):
			return f'\033[92m{val}\033[0m' if val > 0 else f'\033[91m{val}\033[0m'

		trades_df['pnl'] = trades_df['pnl'].apply(color_value)
		trades_df['return_pct'] = trades_df['return_pct'].apply(color_value)

		print("\nTrades:")
		print(tabulate(trades_df, headers='keys', tablefmt='psql'))


	# This function will only plot the market prices of the stock(s)
	def plot_stock_prices(self, price_data):
		"""
		Plots the prices of the stock(s) in the strategy over time
		"""
		# Create the figure and axis
		fig, ax = plt.subplots(figsize=(10, 6))

		# Iterate over the stocks and plot their prices
		for symbol, stock_data in price_data.items():
			ax.plot(stock_data['date'], stock_data['close'], label=f"{symbol} Close Price")

		# Set the labels and title
		ax.set_xlabel('Date')
		ax.set_ylabel('Price')
		ax.set_title('Stock Prices Over Time')
		# Add the legend
		ax.legend()
		# Show the plot
		plt.show()


	# This function will plot the normalised % change of the portfolio value over time and the % change of the stock(s) it trades over time
	def plot_normalized_returns(self, results):
		"""
		Plots the normalized percentage change of portfolio value and stock prices over time
		"""
		fig, ax = plt.subplots(figsize=(12, 6))
		
		# Get portfolio values from results
		portfolio_df = results.portfolio
		
		# Calculate normalized returns for portfolio (starting at 100%)
		initial_value = portfolio_df['market_value'].iloc[0]
		normalized_portfolio = (portfolio_df['market_value'] / initial_value - 1) * 100
		
		# Plot portfolio returns
		ax.plot(portfolio_df.index, normalized_portfolio, label='Portfolio', linewidth=2)
		
		# Get positions DataFrame and unique symbols
		positions_df = results.positions
		unique_symbols = positions_df.index.get_level_values(0).unique()
		
		# For each symbol, plot its normalized price change
		for symbol in unique_symbols:
			# Get price data for this symbol from positions
			symbol_data = positions_df.xs(symbol, level=0)
			
			# Calculate normalized returns (starting at 100%)
			initial_price = symbol_data['close'].iloc[0]
			normalized_prices = (symbol_data['close'] / initial_price - 1) * 100
			
			# Plot the normalized price
			ax.plot(symbol_data.index, normalized_prices, label=f'{symbol}', alpha=0.7)
		
		ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
		ax.set_xlabel('Date')
		ax.set_ylabel('Percentage Change (%)')
		ax.set_title('Normalized Returns: Portfolio vs Stocks')
		ax.legend()
		ax.grid(True, alpha=0.3)
		plt.tight_layout()
		plt.show()




	# This fucntion is my implementation from a previous project to help me work out how to do this, it will be removed later
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
