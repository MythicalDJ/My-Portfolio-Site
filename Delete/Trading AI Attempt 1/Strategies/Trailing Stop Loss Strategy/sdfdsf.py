import pybroker
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig
from pybroker import Alpaca

pybroker.enable_data_source_cache('AlapacaCache')
alpaca = Alpaca('PKVTPHG6Y7UKEKCQH0TH', 'BmL0GiERre6MtIj47ZjOPfygMZMvGOGtRu4cIjBI')
config = StrategyConfig(initial_cash=1000)

##########################################################
#_______________________Settings_________________________#

StockToBuy = 'aapl'
StockToShort = 'tsla'
DateFrom = '1/1/2018'
DateTo = '30/8/2024'
TimeFrame = '1d'

##########################################################

strategy = Strategy(Alpaca('PKVTPHG6Y7UKEKCQH0TH', 'BmL0GiERre6MtIj47ZjOPfygMZMvGOGtRu4cIjBI'), DateFrom, DateTo, config= config)
StockToBuy = StockToBuy.upper()
StockToShort = StockToShort.upper()


def buy_with_trailing_stop_loss_and_profit(ctx):
	if not ctx.long_pos():
		ctx.buy_shares = ctx.calc_target_shares(1)
		ctx.stop_trailing_pct = 0.5
		
def short_with_trailing_stop_loss_and_profit(ctx):
	if not ctx.long_pos():
		ctx.sell_shares = ctx.calc_target_shares(1)
		ctx.stop_trailing_pct = 0.5
		
strategy.clear_executions()
strategy.add_execution(buy_with_trailing_stop_loss_and_profit, [StockToBuy])
strategy.add_execution(short_with_trailing_stop_loss_and_profit, [StockToShort])
result = strategy.backtest(timeframe= TimeFrame , calc_bootstrap=True)
print("\nMetrics\n",result.metrics_df)
print("\nMaximum Drawdown\n",result.bootstrap.drawdown_conf)
print("\nConfidence Intervals\n",result.bootstrap.conf_intervals)

trades_df = pd.DataFrame(result.trades)

# Set display options to show the entire DataFrame
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Function to color rows based on pnl and return_pct values
def color_value(val):
	return f'\033[92m{val}\033[0m' if val > 0 else f'\033[91m{val}\033[0m'

# Apply the color function to the 'pnl' and 'return_pct' columns
trades_df['pnl'] = trades_df['pnl'].apply(color_value)
trades_df['return_pct'] = trades_df['return_pct'].apply(color_value)

# Add a new column for the portfolio value at the exit date of each trade
portfolio_values = []
for exit_date in trades_df['exit_date']:
	portfolio_value = result.portfolio.loc[exit_date, 'market_value']
	portfolio_values.append(portfolio_value)

trades_df['portfolio_value'] = portfolio_values

# Fetch historical price data for the stocks
price_data_buy = alpaca.query(StockToBuy, DateFrom, DateTo, TimeFrame)
price_data_short = alpaca.query(StockToShort, DateFrom, DateTo, TimeFrame)

# Print the styled DataFrame using tabulate
print(tabulate(trades_df, headers='keys', tablefmt='psql'))

# Plot the market value of the portfolio over time
plt.figure(figsize=(10, 6))
plt.plot(result.portfolio.index, result.portfolio['market_value'], label='Market Value')
plt.xlabel('Date')
plt.ylabel('Market Value')
plt.title('Portfolio Market Value Over Time')
plt.legend()
plt.show()