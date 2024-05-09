# filename: get_aapl_stock_prices.py

import yfinance as yf

# Get the historical stock data for AAPL for the last 30 days
aapl = yf.Ticker("AAPL")
historical_data = aapl.history(period="30d")

# Print the historical stock data
print(historical_data)