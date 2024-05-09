# filename: calculate_apple_average.py
import yfinance as yf

# Get the historical stock data for AAPL for the last 30 days
aapl = yf.Ticker("AAPL")
hist = aapl.history(period="1mo")

# Calculate the average closing price for the last 30 days
average_price = hist['Close'].mean()

# Save the average price to a file
with open("apple_average.txt", "w") as file:
    file.write(f"The average price of AAPL stock in the last 30 days is: {average_price}")

print(f"The average price of AAPL stock in the last 30 days is: {average_price}")