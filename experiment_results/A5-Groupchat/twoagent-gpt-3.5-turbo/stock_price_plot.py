# filename: stock_price_plot.py
import yfinance as yf
import matplotlib.pyplot as plt

# Fetching the stock price data for $AAPL for the last 30 days
data = yf.download('AAPL', period='1mo')

# Plotting the stock prices in a line chart
plt.figure(figsize=(12, 6))
plt.plot(data['Close'], label='AAPL Close Price')
plt.title('AAPL Stock Price in the Last 30 Days')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.grid()
plt.savefig('apple.png')
plt.show()