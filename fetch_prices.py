import subprocess
import json
import datetime

def fetch_stock_price(ticker, year, month):
    """Fetches stock price using the ticker price fetcher command-line tool."""
    cmd = ["python", "fetch_price.py", "-j", ticker, str(year), str(month)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return eval(result.stdout)  # Assuming output is in JSON format
    except subprocess.CalledProcessError as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def fetch_exchange_rate(from_currency, to_currency):
    """Fetch exchange rate using the same script."""
    cmd = ["python", "fetch_price.py", "-j", f"{from_currency}{to_currency}=X"]
    if from_currency == to_currency:
        return 1
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        prices = eval(result.stdout)
        return prices["price"]
    except subprocess.CalledProcessError as e:
        print(f"Error fetching exchange rate {from_currency} to {to_currency}: {e}")
        return None

def convert_prices(stock_data, target_currencies):
    """Convert stock prices to target currencies."""
    converted = {}
    for target_currency in target_currencies:
        rate = fetch_exchange_rate(stock_data['currency'], target_currency)
        if rate:
            converted[target_currency] = stock_data['price'] * rate
    return converted

def main():
    tickers = ["VWCE.DE"]  # Example list of stocks
    target_currencies = ["EUR", "HUF"]  # Fixed target currencies
    today = datetime.date.today()
    year, month = today.year, today.month
    
    for ticker in tickers:
        stock_data = fetch_stock_price(ticker, year, month)
        if stock_data:
            converted_prices = convert_prices(stock_data, target_currencies)
            print(f"{ticker} prices converted: {converted_prices}")

if __name__ == "__main__":
    main()

