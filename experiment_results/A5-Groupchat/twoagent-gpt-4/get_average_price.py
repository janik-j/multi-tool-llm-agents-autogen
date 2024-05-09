# filename: get_average_price.py

import yfinance as yf
from datetime import datetime, timedelta

# Define the ticker symbol
tickerSymbol = 'AAPL'

# Get data for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Get the data
tickerData = yf.Ticker(tickerSymbol)
tickerDf = tickerData.history(period='1d', start=start_date, end=end_date)

# Calculate the average price
average_price = tickerDf['Close'].mean()

# Save the result to a file
with open('apple_average.txt', 'w') as f:
    f.write(f'The average price of {tickerSymbol} in the last 30 days is: {average_price}\n')

print('Average price calculated and saved to apple_average.txt')