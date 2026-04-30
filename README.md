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

Tests
-----

```bash
poetry run pytest -v
```
