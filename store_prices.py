from argparse import ArgumentParser
from datetime import date
from pathlib import Path

from fetch_price import fetch_price_for_date
from fetch_prices import (
    Commodity,
    convert_prices_for_date,
    parse_commodities,
)
from ticker import Ticker


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def format_price_line(price_date: str, symbol: str, price: float, currency: str) -> str:
    return f"{price_date} price {symbol}   {price:.02f} {currency}"


def price_line_key(line: str) -> tuple[str, str, str] | None:
    parts = line.split()
    if len(parts) != 5 or parts[1] != "price":
        return None
    return parts[0], parts[2], parts[4]


def upsert_price_lines(path: Path, new_lines: list[str]) -> None:
    new_keys = {price_line_key(line) for line in new_lines}
    existing_lines = path.read_text().splitlines() if path.exists() else []
    kept_lines = [
        line
        for line in existing_lines
        if price_line_key(line) is None or price_line_key(line) not in new_keys
    ]

    path.write_text("\n".join(sorted(kept_lines + new_lines)) + "\n")


def update_year_main(year_dir: Path) -> None:
    includes = [
        f'include "{path.name}"'
        for path in sorted(year_dir.glob("*.beancount"))
        if path.name != "main.beancount"
    ]
    (year_dir / "main.beancount").write_text("\n".join(includes) + "\n")


def price_lines_for_commodity(
    commodity: Commodity,
    stock_data: Ticker,
    converted_prices: dict[str, float],
) -> list[str]:
    lines = [
        format_price_line(
            stock_data.date, commodity.symbol, stock_data.price, stock_data.currency
        )
    ]
    for currency, price in sorted(converted_prices.items()):
        lines.append(format_price_line(stock_data.date, commodity.symbol, price, currency))
    return lines


def store_commodity_prices(output_dir: Path, commodity: Commodity, lines: list[str]) -> None:
    if not lines:
        return

    year = lines[0].split(maxsplit=1)[0][0:4]
    year_dir = output_dir / year
    year_dir.mkdir(parents=True, exist_ok=True)
    upsert_price_lines(year_dir / f"{commodity.symbol}.beancount", lines)
    update_year_main(year_dir)


def fetch_and_store_prices(
    commodities_path: Path,
    output_dir: Path,
    price_date: date,
    target_currencies: list[str],
) -> int:
    stored_count = 0
    commodities = parse_commodities(commodities_path)
    if not commodities:
        raise SystemExit(f"No commodities found in {commodities_path}")

    for commodity in commodities:
        stock_data = fetch_price_for_date(commodity.ticker, price_date)
        if stock_data is None:
            print(f"; Could not retrieve price for ticker: {commodity.ticker}")
            continue

        converted_prices = convert_prices_for_date(
            stock_data, price_date, target_currencies
        )
        lines = price_lines_for_commodity(commodity, stock_data, converted_prices)
        store_commodity_prices(output_dir, commodity, lines)
        for line in lines:
            print(line)
        stored_count += 1

    return stored_count


def main() -> None:
    parser = ArgumentParser(
        description="Fetch daily prices and store them in yearly Beancount files."
    )
    parser.add_argument(
        "--commodities",
        default="commodities.beancount",
        type=Path,
        help="Beancount file containing commodity directives with ticker metadata",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("."),
        type=Path,
        help="Directory where <year>/<ticker>.beancount files are stored",
    )
    parser.add_argument(
        "--date",
        default=date.today(),
        type=parse_date,
        help="Price date to fetch in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--target-currency",
        action="append",
        dest="target_currencies",
        default=None,
        help="Currency to print converted prices for; repeat to specify multiple",
    )
    args = parser.parse_args()

    target_currencies = args.target_currencies or ["EUR", "HUF"]
    fetch_and_store_prices(
        args.commodities,
        args.output_dir,
        args.date,
        target_currencies,
    )


if __name__ == "__main__":
    main()
