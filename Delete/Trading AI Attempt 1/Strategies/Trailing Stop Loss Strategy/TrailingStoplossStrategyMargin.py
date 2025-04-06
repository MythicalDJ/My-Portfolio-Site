import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import config
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig, Alpaca

# Initialize Alpaca
API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY
alpaca = Alpaca(API_KEY, SECRET_KEY)
class Stock:
    def __init__(self, symbol, strategy, trailing_stop_loss_pct):
        self.symbol = symbol
        self.strategy = strategy
        self.trailing_stop_loss_pct = trailing_stop_loss_pct

##########################################################
#_______________________Settings_________________________#

StockToBuy = Stock('aapl','Long', 0.5)
StockToShort = Stock('tsla','long', 0.5)
DateFrom = '1/1/2018'
DateTo = '30/8/2024'
TimeFrame = '1d'

##########################################################

stocks = [StockToBuy, StockToShort]

# Make sure the stock symbols are in uppercase
for stock in stocks:
    stock.symbol = stock.symbol.upper()

# Create strategy
config = StrategyConfig(initial_cash=1000)
strategy = Strategy(alpaca, DateFrom, DateTo, config=config, adjust='all')

# Define execution functions
def buy_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.long_pos():
        ctx.buy_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = StockToBuy.trailing_stop_loss_pct

def short_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.long_pos():
        ctx.sell_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = StockToShort.trailing_stop_loss_pct


# Clear previous executions and add new ones
strategy.clear_executions()
strategy.add_execution(buy_with_trailing_stop_loss_and_profit, [StockToBuy.symbol])
#strategy.add_execution(short_with_trailing_stop_loss_and_profit, [StockToShort.symbol])

# Backtest and get results
result = strategy.backtest(timeframe=TimeFrame, calc_bootstrap=True)

# Save trade data to an Excel file
trades_df = pd.DataFrame(result.trades)
trades_df.to_excel('Excel_Files/trades.xlsx', index=False)

# Fetch historical price data for the stocks
price_data_buy = alpaca.query(StockToBuy.symbol, DateFrom, DateTo, TimeFrame)
price_data_short = alpaca.query(StockToShort.symbol, DateFrom, DateTo, TimeFrame)

# Convert datetime columns to timezone-unaware datetimes
price_data_buy['date'] = price_data_buy['date'].dt.tz_localize(None)
price_data_short['date'] = price_data_short['date'].dt.tz_localize(None)

# Save price data to an Excel file
with pd.ExcelWriter('Excel_Files/price_data.xlsx') as writer:
    price_data_buy.to_excel(writer, sheet_name=f'{StockToBuy.symbol}_prices', index=False)
    price_data_short.to_excel(writer, sheet_name=f'{StockToShort.symbol}_prices', index=False)
    
# Function to color rows based on pnl and return_pct values
def color_value(val):
	return f'\033[92m{val}\033[0m' if val > 0 else f'\033[91m{val}\033[0m'

# Apply the color function to the 'pnl' and 'return_pct' columns
trades_df['pnl'] = trades_df['pnl'].apply(color_value)
trades_df['return_pct'] = trades_df['return_pct'].apply(color_value)

# Print trade data using tabulate
print(tabulate(trades_df, headers='keys', tablefmt='psql'))

# Plot portfolio market value over time
plt.figure(figsize=(10, 6))
plt.plot(result.portfolio.index, result.portfolio['market_value'], label='Market Value')
plt.xlabel('Date')
plt.ylabel('Market Value')
plt.title('Portfolio Market Value Over Time')
plt.legend()
plt.show()
