import json
from datetime import datetime, date

class TradeInfo:
	def __init__(self, filename='trade_info.json'):
		self.filename = filename
		self.data = self.load_data()
		if self.data['first_run_date'] is None:
			self.set_first_run_date()

	def load_data(self):
		try:
			with open(self.filename, 'r') as f:
				return json.load(f)
		except FileNotFoundError:
			return {
				'first_run_date': None,
				'last_trade_date': None,
				'current_positions': {}
			}

	def save_data(self):
		with open(self.filename, 'w') as f:
			json.dump(self.data, f, default=str)

	def set_first_run_date(self):
		self.data['first_run_date'] = datetime.now().strftime('%Y-%m-%d')
		self.save_data()

	def update_trade_dates(self, trade_date):
		trade_date = trade_date.strftime('%Y-%m-%d') if isinstance(trade_date, (datetime, date)) else trade_date
		self.data['last_trade_date'] = trade_date
		self.save_data()

	def update_position(self, symbol, shares, entry_price):
		self.data['current_positions'][symbol] = {
			'shares': shares,
			'entry_price': entry_price
		}
		self.save_data()

	def remove_position(self, symbol):
		if symbol in self.data['current_positions']:
			del self.data['current_positions'][symbol]
			self.save_data()

	def get_positions(self):
		return self.data['current_positions']

	def get_first_run_date(self):
		return self.data['first_run_date']

	def get_last_trade_date(self):
		return self.data['last_trade_date']