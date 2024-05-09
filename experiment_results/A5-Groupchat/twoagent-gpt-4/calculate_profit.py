# filename: calculate_profit.py

import yfinance as yf
from datetime import datetime, timedelta

# Define the ticker symbol
tickerSymbol = 'AAPL'

# Get data for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Get the historical prices for this ticker
tickerData = yf.Ticker(tickerSymbol)
tickerDf = tickerData.history(period='1d', start=start_date, end=end_date)

# Find the lowest and highest prices
lowest_price = tickerDf['Low'].min()
highest_price = tickerDf['High'].max()

# Calculate the profit
stocks = 200
profit = (highest_price - lowest_price) * stocks

# Save the result to a file
with open('apple_profit.txt', 'w') as f:
    f.write(f'Profit: ${profit}\n')

print('The profit has been calculated and saved to apple_profit.txt.')