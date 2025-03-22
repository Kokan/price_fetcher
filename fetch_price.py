import yfinance
import pandas
from datetime import datetime
import argparse

def fetch_first_day_of_month_price(ticker: str, year: int, month: int):
    try:
        # Get the current date and calculate the first day of the month
        first_day_of_month = datetime(year, month, 1)

        start_date = first_day_of_month.strftime('%Y-%m-%d')
        end_date = (first_day_of_month + pandas.Timedelta(days=7)).strftime('%Y-%m-%d')

        currency = yfinance.Ticker(ticker).info['currency']
        stock_data = yfinance.download(ticker, start=start_date, end=end_date, rounding=True, interval="1d", auto_adjust=False, progress=False)

        # Ensure data is available
        if stock_data.empty:
            return None

        first_day_price = stock_data['Close'].iloc[0]
        return {"ticker": ticker,
                "price": float(first_day_price[ticker]),
                "date": str(first_day_price.name),
                "currency": currency}

    except Exception as e:
        print(f"; An error occurred for ticker {ticker}: {e}")
        return None

def format_json(ticker):
    print(ticker)
    return

def format_beancount(ticker):
    #2023-01-02 price VWCE	92.26 EUR
    print(f"{ticker['date'][0:10]} price {ticker['ticker']}\t{ticker['price']} {ticker['currency']}")
    return

def format_text(ticker):
    print(f"Ticker: {ticker['ticker']} Price: {ticker['price']} Date: {ticker['date']}")
    return

def main(args):
    # Load tickers from a file

    yfinance.set_tz_cache_location(args.cache)

    if args.beancount:
        print(f"; Fetching data for ticker: {args.ticker}")
    try:
        first_day_price = fetch_first_day_of_month_price(args.ticker, args.year, args.month)
        if first_day_price is None:
            print(f"; Could not retrieve price for ticker: {args.ticker}")
            return -1

        if args.beancount:
            format_beancount(first_day_price)
        elif args.json:
            format_json(first_day_price)
        else:
            format_text(first_day_price)
    except Exception as e:
        print(f"; Error fetching data for {args.ticker}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='ticker price fetcher',
                    description='Fetches a specific ticker prices of the current month')

    parser.add_argument('ticker')
    parser.add_argument('year',  type=int, nargs='?', default=datetime.now().year)
    parser.add_argument('month', type=int, nargs='?', default=datetime.now().month)
    parser.add_argument('-b', '--beancount', action='store_true')
    parser.add_argument('-j', '--json', action='store_true')
    parser.add_argument('-c', '--cache', type=str, default='.yfinance-cache/')
    
    main(parser.parse_args())

