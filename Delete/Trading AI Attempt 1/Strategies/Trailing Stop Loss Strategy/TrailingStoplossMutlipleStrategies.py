import pandas as pd
import sys
sys.path.append('C:/Users/Toby/Documents/Trading AI')
import config
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pybroker
from tabulate import tabulate
from pybroker import Strategy, StrategyConfig, Alpaca

# Initialize Alpaca
API_KEY = config.APCA_API_KEY
SECRET_KEY = config.APCA_API_SECRET_KEY
alpaca = Alpaca(API_KEY, SECRET_KEY)
alpaca.adjust = 'all'
pybroker.enable_data_source_cache('AlpacaCache')

class Stock:
    def __init__(self, symbol, strategy, trailing_stop_loss_pct):
        self.symbol = symbol
        self.strategy = strategy
        self.trailing_stop_loss_pct = trailing_stop_loss_pct
##########################################################
#_______________________Settings_________________________#

StockOne = Stock('spy','Long', 0.25)
StockTwo = Stock('intc','Long', 0.25)
StockThree = Stock('msft','Long', 0.25)
StockFour = Stock('aapl','Long', 0.25)
#StockFive = Stock('amd','Long', 0.25)
#StockSix = Stock('tsla','Long', 0.25)

DateFrom = '1/1/2018'

DateTo = '30/8/2024'
TimeFrame = '1d'

##########################################################

# Convert all stock symbols to uppercase
stocks = [StockOne, StockTwo, StockThree, StockFour]

for stock in stocks:
    stock.symbol = stock.symbol.upper()

# Create separate configurations and strategies for each stock
configs = {stock: StrategyConfig(initial_cash=1000) for stock in stocks}
strategies = {stock: Strategy(Alpaca(API_KEY, SECRET_KEY), DateFrom, DateTo, config=configs[stock], adjust='all') for stock in stocks}


# Define execution functions
def buy_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.long_pos():
        ctx.buy_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = next(stock.trailing_stop_loss_pct for stock in stocks if stock.symbol == ctx.symbol)

def short_with_trailing_stop_loss_and_profit(ctx):
    if not ctx.short_pos():
        ctx.sell_shares = ctx.calc_target_shares(1)
        ctx.stop_trailing_pct = next(stock.trailing_stop_loss_pct for stock in stocks if stock.symbol == ctx.symbol)

def reactive_trailing_stop_loss_and_profit(ctx):
	if not hasattr(ctx, 'prev_win_rt'):
		ctx.prev_win_rt = 0
	for stock in stocks:
		if ctx.symbol == stock.symbol and stock.strategy == 'Reactive':
			if ctx.win_rate >= ctx.prev_win_rt:
				buy_with_trailing_stop_loss_and_profit(ctx)
			else:
				short_with_trailing_stop_loss_and_profit(ctx)
			ctx.prev_win_rt = ctx.win_rate

# Clear previous executions and add new ones
for stock, strategy in strategies.items():
    strategy.clear_executions()
    if stock.strategy == 'Long':
        strategy.add_execution(buy_with_trailing_stop_loss_and_profit, stock.symbol)
    elif stock.strategy == 'Short':
        strategy.add_execution(short_with_trailing_stop_loss_and_profit, stock.symbol)
    elif stock.strategy == 'Reactive':
        strategy.add_execution(reactive_trailing_stop_loss_and_profit, stock.symbol)

# Run backtest for each strategy
results = {stock: strategy.backtest(timeframe=TimeFrame, calc_bootstrap=True) for stock, strategy in strategies.items()}

# Combine trade data from all strategies
all_trades = pd.concat([pd.DataFrame(result.trades) for result in results.values()])
all_trades.to_excel('Excel_Files/TrailingStopLossStrategy - Multiple Stocks.xlsx', index=False)

# Fetch and save historical price data for the stocks
price_data = {}
for stock in stocks:
    price_data[stock] = alpaca.query(stock.symbol, DateFrom, DateTo, TimeFrame, adjust='all')
    price_data[stock]['date'] = price_data[stock]['date'].dt.tz_localize(None)

with pd.ExcelWriter('Excel_Files/price_data.xlsx') as writer:
    for stock, data in price_data.items():
        data.to_excel(writer, sheet_name=f'{stock.symbol}_prices', index=False)

# Combine and save portfolio data
all_portfolios = pd.concat([result.portfolio for result in results.values()], axis=1)
all_portfolios.columns.symbol = stocks
all_portfolios.to_excel('Excel_Files/portfolio_data.xlsx', index=True)

def print_results(results, strategy_name):
    print(f"\n{strategy_name} Strategy Results")
    
    # Combine metrics from all strategies
    all_metrics = pd.concat([result.metrics_df for result in results.values()], axis=1)
    all_metrics.columns.symbol = [stock.symbol for stock in stocks]
    print("\nMetrics\n", all_metrics)

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

    # New code: Plot price data for all stocks in a separate window
    plt.figure(figsize=(12, 6))
    for stock, data in price_data.items():
        plt.plot(data['date'], data['close'], label=f"{stock.symbol} Close Price")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('Stock Prices Over Time')
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

# Call the function with the results
print_results(results, "Trailing Stop Loss")