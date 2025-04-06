import pandas as pd
import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import config
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig, Alpaca

API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY
# Initialize Alpaca
alpaca = Alpaca(API_KEY, SECRET_KEY)

##########################################################
#_______________________Settings_________________________#
StockToBuy = 'aapl'
StockToShort = 'tsla'
DateFrom = '1/1/2018'
DateTo = '30/8/2024'
TimeFrame = '1d'
##########################################################

# Make sure the stock symbols are in uppercase
StockToBuy = StockToBuy.upper()
StockToShort = StockToShort.upper()

# Create strategy
LongConfig = StrategyConfig(initial_cash=500)
LongStrategy = Strategy(alpaca, DateFrom, DateTo, config=LongConfig)
ShortConfig = StrategyConfig(initial_cash=500)
ShortStrategy = Strategy(alpaca, DateFrom, DateTo, config=ShortConfig)


# Define execution functions
def buy_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.long_pos():
        ctx.buy_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = 0.5

def short_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.short_pos():
        ctx.sell_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = 0.5

# Clear previous executions and add new ones
LongStrategy.clear_executions()
ShortStrategy.clear_executions()
LongStrategy.add_execution(buy_with_trailing_stop_loss_and_profit, [StockToBuy])
ShortStrategy.add_execution(short_with_trailing_stop_loss_and_profit, [StockToShort])

# Backtest and get results
LongResult = LongStrategy.backtest(timeframe=TimeFrame, calc_bootstrap=True)
ShortResult = ShortStrategy.backtest(timeframe=TimeFrame, calc_bootstrap=True)

#temporarily save the index of the portfolio
temp_long_index = LongResult.portfolio.index
temp_short_index = ShortResult.portfolio.index

# Save Long trade data to an Excel file
LongResult.portfolio.reset_index(inplace=True)
long_trades_df = pd.DataFrame(LongResult.trades)
long_trades_df['portfolio_value'] = LongResult.portfolio.loc[long_trades_df.index, 'market_value']
long_trades_df['purchase_cost'] = long_trades_df['shares'] * long_trades_df['entry']
long_trades_df.to_excel('Excel_Files/LongTrades.xlsx', index=False)

# Save Short trade data to an Excel file
ShortResult.portfolio.reset_index(inplace=True)
short_trades_df = pd.DataFrame(ShortResult.trades)
short_trades_df['portfolio_value'] = ShortResult.portfolio.loc[short_trades_df.index, 'market_value']
short_trades_df['purchase_cost'] = short_trades_df['shares'] * short_trades_df['entry']
short_trades_df.to_excel('Excel_Files/ShortTrades.xlsx', index=False)


# Fetch historical price data for the stocks
price_data_buy = alpaca.query(StockToBuy, DateFrom, DateTo, TimeFrame)
price_data_short = alpaca.query(StockToShort, DateFrom, DateTo, TimeFrame)

# Temprarily hold the timezone aware dates
temp_price_data_buy = price_data_buy['date']
temp_price_data_short = price_data_short['date']

# Convert datetime columns to timezone-unaware datetimes
price_data_buy['date'] = price_data_buy['date'].dt.tz_localize(None)
price_data_short['date'] = price_data_short['date'].dt.tz_localize(None)

# Save price data to an Excel file
with pd.ExcelWriter('Excel_Files/price_data.xlsx') as writer:
    price_data_buy.to_excel(writer, sheet_name=f'{StockToBuy}_prices', index=False)
    price_data_short.to_excel(writer, sheet_name=f'{StockToShort}_prices', index=False)

# revert the indexes of the portfolio
LongResult.portfolio.index = temp_long_index
ShortResult.portfolio.index = temp_short_index

# Function to color rows based on pnl and return_pct values
def color_value(val):
    return f'\033[92m{val}\033[0m' if val > 0 else f'\033[91m{val}\033[0m'

# Apply the color function to the 'pnl' and 'return_pct' columns
long_trades_df['pnl'] = long_trades_df['pnl'].apply(color_value)
short_trades_df['pnl'] = short_trades_df['pnl'].apply(color_value)
short_trades_df['return_pct'] = short_trades_df['return_pct'].apply(color_value)
long_trades_df['return_pct'] = long_trades_df['return_pct'].apply(color_value)

# Print trade data using tabulate
print(tabulate(long_trades_df, headers='keys', tablefmt='psql'))
print(tabulate(short_trades_df, headers='keys', tablefmt='psql'))

# Plot Long portfolio market value over time
plt.figure(figsize=(10, 6))
plt.plot(LongResult.portfolio.index, LongResult.portfolio['market_value'], label='Long Portfolio', color= "green")
plt.plot(ShortResult.portfolio.index, ShortResult.portfolio['market_value'], label='Short Portfolio', color = "red")
plt.plot(LongResult.portfolio.index, LongResult.portfolio['market_value'] + ShortResult.portfolio['market_value'], label='Total Portfolio', color = "purple")

# Set the x-axis to display dates
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gcf().autofmt_xdate()  # Slant the dates for better readability

plt.xlabel('Date')
plt.ylabel('Market Value')
plt.title('Portfolio Market Value Over Time')
plt.legend()
plt.show()