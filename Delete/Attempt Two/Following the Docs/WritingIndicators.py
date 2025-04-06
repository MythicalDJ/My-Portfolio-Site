import numpy as np
import pybroker
from numpy import njit

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
