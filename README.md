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

Tests
-----

```bash
poetry run pytest -v
```
