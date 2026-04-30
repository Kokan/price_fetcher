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


DEFAULT_CURRENCY_PAIRS = (("EUR", "HUF"), ("USD", "HUF"))
PRICE_AMOUNT_WIDTH = 18
PRICE_SYMBOL_WIDTH = 12


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def format_price_line(
    price_date: str, symbol: str, price: float, currency: str, precision: int = 2
) -> str:
    return format_price_amount(
        price_date, symbol, f"{price:.{precision}f}", currency
    )


def format_price_amount(price_date: str, symbol: str, amount: str, currency: str) -> str:
    return (
        f"{price_date} price {symbol:<{PRICE_SYMBOL_WIDTH}} "
        f"{amount:>{PRICE_AMOUNT_WIDTH}} {currency}"
    )


def format_existing_price_line(line: str) -> str:
    key = price_line_key(line)
    if key is None:
        return line

    price_date, symbol, currency = key
    amount = line.split()[3]
    return format_price_amount(price_date, symbol, amount, currency)


def price_line_key(line: str) -> tuple[str, str, str] | None:
    parts = line.split()
    if len(parts) != 5 or parts[1] != "price":
        return None
    return parts[0], parts[2], parts[4]


def price_line_amount(line: str) -> str | None:
    if price_line_key(line) is None:
        return None
    return line.split()[3]


def upsert_price_lines(path: Path, new_lines: list[str]) -> None:
    existing_lines = path.read_text().splitlines() if path.exists() else []
    existing_by_key = {
        key: line
        for line in existing_lines
        if (key := price_line_key(line)) is not None
    }

    replacements_by_key = {}
    new_lines_without_key = []
    for new_line in new_lines:
        key = price_line_key(new_line)
        if key is None:
            new_lines_without_key.append(new_line)
            continue

        existing_line = existing_by_key.get(key)
        if (
            existing_line is not None
            and price_line_amount(existing_line) == price_line_amount(new_line)
        ):
            continue

        replacements_by_key[key] = new_line

    merged_lines = []
    replaced_keys = set()
    for existing_line in existing_lines:
        key = price_line_key(existing_line)
        if key in replacements_by_key:
            merged_lines.append(replacements_by_key[key])
            replaced_keys.add(key)
        else:
            merged_lines.append(existing_line)

    merged_lines.extend(new_lines_without_key)
    merged_lines.extend(
        line
        for key, line in replacements_by_key.items()
        if key not in replaced_keys
    )

    contents = "\n".join(merged_lines) + "\n"
    if not path.exists() or path.read_text() != contents:
        path.write_text(contents)


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


def store_price_lines(output_dir: Path, symbol: str, lines: list[str]) -> None:
    if not lines:
        return

    year = lines[0].split(maxsplit=1)[0][0:4]
    year_dir = output_dir / year
    year_dir.mkdir(parents=True, exist_ok=True)
    upsert_price_lines(year_dir / f"{symbol}.beancount", lines)
    update_year_main(year_dir)


def store_commodity_prices(output_dir: Path, commodity: Commodity, lines: list[str]) -> None:
    store_price_lines(output_dir, commodity.symbol, lines)


def currency_pair_price_lines(
    base_currency: str, quote_currency: str, rate_data: Ticker
) -> dict[str, list[str]]:
    return {
        base_currency: [
            format_price_line(
                rate_data.date,
                base_currency,
                rate_data.price,
                quote_currency,
                precision=8,
            )
        ],
    }


def fetch_and_store_currency_rates(
    output_dir: Path, price_date: date, currency_pairs: list[tuple[str, str]]
) -> int:
    stored_count = 0
    lines_by_symbol: dict[str, list[str]] = {}

    for base_currency, quote_currency in currency_pairs:
        rate_data = fetch_price_for_date(
            f"{base_currency}{quote_currency}=X", price_date
        )
        if rate_data is None:
            print(f"; Could not retrieve exchange rate: {base_currency}/{quote_currency}")
            continue

        for symbol, lines in currency_pair_price_lines(
            base_currency, quote_currency, rate_data
        ).items():
            lines_by_symbol.setdefault(symbol, []).extend(lines)

    for symbol, lines in lines_by_symbol.items():
        store_price_lines(output_dir, symbol, lines)
        for line in lines:
            print(line)
        stored_count += 1

    return stored_count


def fetch_and_store_prices(
    commodities_path: Path,
    output_dir: Path,
    price_date: date,
    target_currencies: list[str],
    currency_pairs: list[tuple[str, str]],
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

    stored_count += fetch_and_store_currency_rates(
        output_dir, price_date, currency_pairs
    )
    return stored_count


def parse_currency_pair(value: str) -> tuple[str, str]:
    currencies = value.split(":", maxsplit=1)
    if len(currencies) != 2 or not all(currencies):
        raise ValueError("Currency pairs must use BASE:QUOTE format")
    return currencies[0].upper(), currencies[1].upper()


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
        default=Path("prices"),
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
    parser.add_argument(
        "--currency-pair",
        action="append",
        dest="currency_pairs",
        default=None,
        type=parse_currency_pair,
        help="Currency pair to store as BASE priced in QUOTE",
    )
    args = parser.parse_args()

    target_currencies = args.target_currencies or ["EUR", "HUF"]
    currency_pairs = args.currency_pairs or list(DEFAULT_CURRENCY_PAIRS)
    fetch_and_store_prices(
        args.commodities,
        args.output_dir,
        args.date,
        target_currencies,
        currency_pairs,
    )


if __name__ == "__main__":
    main()
