# filename: stock_price.py

import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Define the ticker symbol
tickerSymbol = 'AAPL'

# Get data for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Get the data
tickerData = yf.Ticker(tickerSymbol)
tickerDf = tickerData.history(period='1d', start=start_date, end=end_date)

# Plot the close price
plt.figure(figsize=(10,6))
plt.plot(tickerDf['Close'])
plt.title('AAPL Close Price')
plt.xlabel('Date')
plt.ylabel('Close Price (USD)')
plt.grid(True)
plt.savefig('apple.png')