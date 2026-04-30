from datetime import datetime
from fetch_price import fetch_first_day_of_month_price
from ticker import Ticker
import argparse
from typing import Optional


def fetch_stock_price(ticker: str, year: int, month: int) -> Optional[Ticker]:
    return fetch_first_day_of_month_price(ticker, year, month)


def fetch_exchange_rate(
    from_currency: str, to_currency: str, year: int, month: int
) -> Optional[float]:
    if from_currency == to_currency:
        return 1

    ticker = f"{from_currency}{to_currency}=X"
    result = fetch_first_day_of_month_price(ticker, year, month)
    if result is None:
        print(f"Error fetching exchange rate {from_currency} to {to_currency}")
        return None
    return result.price


def convert_prices(
    stock_data: Ticker, year: int, month: int, target_currencies: list[str]
) -> dict[str, float]:
    converted = {}
    for target_currency in target_currencies:
        rate = fetch_exchange_rate(stock_data.currency, target_currency, year, month)
        if rate is not None:
            converted[target_currency] = stock_data.price * rate
    return converted


def main(args):
    tickers = {
        "EUDV.MI": "EUDV",
        "FWRA.MI": "FWRA",
        "MOL.BD": "MOL",
        "KO": "KO",
        "SPPY.DE": "SPPY",
        "STRT.BD": "STRT",
        "VGWD.DE": "VHYL",
        "VUAA.MI": "VUAA",
        "VWCE.DE": "VWCE",
        "WEBN.DE": "WEBN",
        "L8I3.DE": "CSH",
        "SPYW.DE": "SPDR",
        "AMD": "AMD",
        "EURHUF=X": "EUR",
        "USDHUF=X": "USD",
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
                if currency in converted_prices:
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
