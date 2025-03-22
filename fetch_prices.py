from datetime import datetime
from fetch_price import fetch_first_day_of_month_price
from ticker import Ticker
import argparse
import subprocess


def fetch_stock_price(ticker: str, year: int, month: int):
    try:
        return fetch_first_day_of_month_price(ticker, year, month)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def fetch_exchange_rate(from_currency: str, to_currency: str, year: int, month: int):
    if from_currency == to_currency:
        return 1

    ticker = f"{from_currency}{to_currency}=X"
    try:
        result = fetch_first_day_of_month_price(ticker, year, month)
        return result.price
    except subprocess.CalledProcessError as e:
        print(f"Error fetching exchange rate {from_currency} to {to_currency}: {e}")
        return None


def convert_prices(stock_data: Ticker, year: int, month: int, target_currencies: list):
    converted = {}
    for target_currency in target_currencies:
        rate = fetch_exchange_rate(stock_data.currency, target_currency, year, month)
        if rate:
            converted[target_currency] = stock_data.price * rate
    return converted


def main(args):
    tickers = {
        # "EUDV.MI": "EUDV",
        # "FWRA.MI": "FWRA",
        # "MOL.BD": "MOL",
        # "KO": "KO",
        # "SPPY.DE": "SPPY",
        # "STRT.BD": "STRT",
        # "VGWD.DE": "VHYL",
        # "VUAA.MI": "VUAA",
        # "VWCE.DE": "VWCE",
        # "L8I3.DE": "CSH",
        "AMD": "AMD",
    }

    target_currencies = ["EUR", "HUF"]

    for ticker in tickers:
        stock_data = fetch_stock_price(ticker, args.year, args.month)
        if stock_data:
            converted_prices = convert_prices(
                stock_data, args.year, args.month, target_currencies
            )
            print(
                f"{stock_data.date} price {tickers[ticker]}   {stock_data.price:.02f} {stock_data.currency}"
            )
            for currency in target_currencies:
                print(
                    f"{stock_data.date} price {tickers[ticker]}   {converted_prices[currency]:.02f} {currency}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ticker price fetcher",
        description="Fetches a specific ticker prices of the current month",
    )

    parser.add_argument("year", type=int, nargs="?", default=datetime.now().year)
    parser.add_argument("month", type=int, nargs="?", default=datetime.now().month)

    main(parser.parse_args())
