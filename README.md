Price Fetcher
=============

Small Python CLI utilities for fetching ticker prices with `yfinance` and
printing them as plain text, JSON, or Beancount `price` directives.

Setup
-----

```bash
poetry install
```

Usage
-----

Fetch one ticker, defaulting to the current year and month:

```bash
poetry run python fetch_price.py VWCE.DE
```

Fetch one ticker for a specific month:

```bash
poetry run python fetch_price.py VWCE.DE 2024 1
```

Print Beancount output:

```bash
poetry run python fetch_price.py --beancount VWCE.DE 2024 1
```

Run the batch fetcher:

```bash
poetry run python fetch_prices.py 2024 1
```

By default the batch fetcher reads commodity directives from
`commodities.beancount`. If the Beancount commodity name differs from the Yahoo
symbol, add a `ticker` metadata entry. Commodity directives without `ticker`
metadata are skipped.

```beancount
2023-07-01 commodity VWCE
  name: "Vanguard All-World FTSE ETF"
  asset-class: "stock"
  ticker: "VWCE.DE"
```

Use a different commodity file or converted currencies with:

```bash
poetry run python fetch_prices.py 2024 1 --commodities ledger.beancount --target-currency EUR --target-currency HUF
```

Store daily prices in yearly Beancount files:

```bash
poetry run python store_prices.py --date 2026-04-30
```

This writes one file per commodity, for example `prices/2026/VWCE.beancount`,
and maintains `prices/2026/main.beancount` with includes for that year's
commodity files. It also maintains `prices/main.beancount` with includes for
each year, adding new years automatically when they are first generated.
It also stores EUR/HUF and USD/HUF exchange rates, for example
`prices/2026/EUR.beancount` and `prices/2026/USD.beancount`.
The GitHub Actions workflow runs this command daily and commits changed price
files when new prices are available.

Use `--currency-pair BASE:QUOTE` to override the stored exchange-rate pairs.

Validate generated Beancount files with:

```bash
poetry run python validate_prices.py
```

Tests
-----

```bash
poetry run pytest -v
```
