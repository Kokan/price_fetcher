from dataclasses import dataclass
from datetime import datetime
from fetch_price import fetch_first_day_of_month_price
from ticker import Ticker
import argparse
from pathlib import Path
import re
from typing import Optional


COMMODITY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s+commodity\s+(\S+)\s*$")
METADATA_RE = re.compile(r"^\s+([A-Za-z][\w-]*):\s*(.*?)\s*$")


@dataclass(frozen=True)
class Commodity:
    symbol: str
    ticker: str


def parse_metadata_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def parse_commodities(path: str | Path) -> list[Commodity]:
    commodities = []
    current_symbol = None
    current_metadata = {}

    def append_current_commodity():
        if current_symbol is None:
            return

        ticker = current_metadata.get("ticker")
        if ticker is None:
            return

        commodities.append(Commodity(symbol=current_symbol, ticker=ticker))

    for line in Path(path).read_text().splitlines():
        commodity_match = COMMODITY_RE.match(line)
        if commodity_match:
            append_current_commodity()
            current_symbol = commodity_match.group(1)
            current_metadata = {}
            continue

        if current_symbol is None:
            continue

        metadata_match = METADATA_RE.match(line)
        if metadata_match:
            key, value = metadata_match.groups()
            current_metadata[key] = parse_metadata_value(value)

    append_current_commodity()
    return commodities


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
    commodities = parse_commodities(args.commodities)
    if not commodities:
        raise SystemExit(f"No commodities found in {args.commodities}")

    target_currencies = args.target_currencies or ["EUR", "HUF"]

    for commodity in commodities:
        stock_data = fetch_stock_price(commodity.ticker, args.year, args.month)
        if stock_data:
            converted_prices = convert_prices(
                stock_data, args.year, args.month, target_currencies
            )
            print(
                f"{stock_data.date} price {commodity.symbol}   {stock_data.price:.02f} {stock_data.currency}"
            )
            for currency in target_currencies:
                if currency in converted_prices:
                    print(
                        f"{stock_data.date} price {commodity.symbol}   {converted_prices[currency]:.02f} {currency}"
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ticker price fetcher",
        description="Fetches a specific ticker prices of the current month",
    )

    parser.add_argument("year", type=int, nargs="?", default=datetime.now().year)
    parser.add_argument("month", type=int, nargs="?", default=datetime.now().month)
    parser.add_argument(
        "-c",
        "--commodities",
        default="commodities.beancount",
        help="Beancount file containing commodity directives",
    )
    parser.add_argument(
        "--target-currency",
        action="append",
        dest="target_currencies",
        help="Currency to print converted prices for; repeat to specify multiple",
    )

    main(parser.parse_args())
