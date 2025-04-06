import numpy as np
import pandas as pd
import pybroker
from numba import njit
from pybroker import Strategy, StrategyConfig, YFinance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

pybroker.enable_caches("walk_forward_strategy")

def cmma(bar_data, lookback):
	@njit
	def vec_cmma(values):
		# Initialise the result array.
		n = len(values)
		out = np.array([np.nan for _ in range(n)])
		
		# For all bars starting at lookback:
		for i in range(lookback, n):
			# Calculate the moving average for the lookback
			ma = 0
			for j in range (i - lookback, i):
				ma += values[j]
			ma /= lookback
			# Subtract the moving average from value.
			out[i] = values[i] - ma

		return out
	# Calculate with close prices.
	return vec_cmma(bar_data.close)

cmma_20 = pybroker.indicator('cmma_20', cmma, lookback=20)


def train_slr(symbol, train_data, test_data):
	# Train
	# Previous day close prices.
	train_prev_close = train_data['close'].shift(1)
	# Calculate Daily returns.
	train_daily_returns = (train_data['close'] - train_prev_close) / train_prev_close
	# Predict next day's return.
	train_data['pred'] = train_daily_returns.shift(-1)
	train_data =  train_data.dropna()
	# Train LinerRegession model to predict the next day's return
	# given the 20-day CMMA.
	X_train = train_data[['cmma_20']]
	y_train = train_data[['pred']]
	model = LinearRegression()
	model.fit(X_train, y_train)
	# Test
	test_prev_close = test_data['close'].shift(1)
	test_daily_returns = (test_data['close'] - test_prev_close) / test_prev_close
	test_data['pred'] = test_daily_returns.shift(-1)
	test_data = test_data.dropna()
	X_test = test_data[['cmma_20']]
	y_test = test_data[['pred']]
	# Make predictions from test data.
	y_pred = model.predict(X_test)
	# Print goodness of fit
	r2 = r2_score(y_test, np.squeeze(y_pred))
	print(symbol, f'R^2={r2}')

	# Return the trained model and columns to use as input data
	return model, ['cmma_20']


def buy_long(ctx):
	if not ctx.long_pos():
		# Buy if the next bar is predicted to have a positive return:
		if ctx.preds('slr')[-1] > 0:
			ctx.buy_shares = 100
		else:
			# Sell if the next bar is predicted to have a negative return:
			if ctx.preds('slr')[-1] < 0:
				ctx.sell_shares = 100





model_slr = pybroker.model(name='slr', fn=train_slr, indicators=[cmma_20])

config = StrategyConfig(bootstrap_sample_size=100)
strategy = Strategy(YFinance(), '3/1/2017', '3/1/2022', config)

strategy.clear_executions()
strategy.add_execution(buy_long, ['NVDA', 'AMD'], models=model_slr)

result = strategy.walkforward(
	warmup=20,
	windows=3,
	train_size=0.5,
	lookahead=1,
	calc_bootstrap=True,
)


