import json
from types import SimpleNamespace

import pandas

import fetch_price
import fetch_prices
from fetch_prices import Commodity
from ticker import Ticker, format_beancount, format_json, format_text


class FakeYFinanceTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = {"currency": "EUR"}


def test_ticker_formatters():
    ticker = Ticker("VWCE.DE", 99.12, "EUR", "2024-01-02")

    assert json.loads(format_json(ticker)) == {
        "name": "VWCE.DE",
        "price": 99.12,
        "currency": "EUR",
        "date": "2024-01-02",
    }
    assert format_beancount(ticker) == "2024-01-02 price VWCE.DE\t99.12 EUR"
    assert format_text(ticker) == "Ticker: VWCE.DE Price: 99.12 Date: 2024-01-02"


def test_fetch_first_day_of_month_price_uses_first_available_close(monkeypatch):
    def fake_download(ticker, start, end, rounding, interval, auto_adjust, progress):
        assert ticker == "VWCE.DE"
        assert start == "2024-01-01"
        assert end == "2024-01-08"
        assert rounding is True
        assert interval == "1d"
        assert auto_adjust is False
        assert progress is False

        columns = pandas.MultiIndex.from_tuples([("Close", "VWCE.DE")])
        return pandas.DataFrame(
            [[99.12]],
            index=[pandas.Timestamp("2024-01-02")],
            columns=columns,
        )

    monkeypatch.setattr(fetch_price.yfinance, "Ticker", FakeYFinanceTicker)
    monkeypatch.setattr(fetch_price.yfinance, "download", fake_download)

    result = fetch_price.fetch_first_day_of_month_price("VWCE.DE", 2024, 1)

    assert result == Ticker("VWCE.DE", 99.12, "EUR", "2024-01-02")


def test_fetch_first_day_of_month_price_returns_none_for_empty_data(monkeypatch):
    monkeypatch.setattr(fetch_price.yfinance, "Ticker", FakeYFinanceTicker)
    monkeypatch.setattr(
        fetch_price.yfinance,
        "download",
        lambda *args, **kwargs: pandas.DataFrame(),
    )

    result = fetch_price.fetch_first_day_of_month_price("VWCE.DE", 2024, 1)

    assert result is None


def test_fetch_first_day_of_month_price_handles_single_level_close(monkeypatch):
    monkeypatch.setattr(fetch_price.yfinance, "Ticker", FakeYFinanceTicker)
    monkeypatch.setattr(
        fetch_price.yfinance,
        "download",
        lambda *args, **kwargs: pandas.DataFrame(
            {"Close": [42.5]},
            index=[pandas.Timestamp("2024-01-02")],
        ),
    )

    result = fetch_price.fetch_first_day_of_month_price("VWCE.DE", 2024, 1)

    assert result == Ticker("VWCE.DE", 42.5, "EUR", "2024-01-02")


def test_parse_commodities_uses_ticker_metadata(tmp_path):
    commodities_file = tmp_path / "commodities.beancount"
    commodities_file.write_text(
        """
;; COMMODITIES

2023-07-01 commodity VWCE
  name: "Vanguard All-World FTSE ETF"
  asset-class: "stock"
  ticker: "VWCE.DE"
2023-07-01 commodity AMD
  name: "Advanced Micro Devices"
  asset-class: "stock"
2023-07-01 commodity CSH
  name: "Amundi EUR Overnight Return UCITS ETF Acc"
  yahoo: "L8I3.DE"
""".strip()
    )

    commodities = fetch_prices.parse_commodities(commodities_file)

    assert commodities == [
        Commodity(symbol="VWCE", ticker="VWCE.DE"),
    ]


def test_convert_prices_skips_missing_exchange_rates(monkeypatch):
    def fake_fetch_exchange_rate(from_currency, to_currency, year, month):
        rates = {"HUF": None}
        return rates[to_currency]

    monkeypatch.setattr(fetch_prices, "fetch_exchange_rate", fake_fetch_exchange_rate)

    converted = fetch_prices.convert_prices(
        Ticker("VWCE.DE", 10.0, "EUR", "2024-01-02"),
        2024,
        1,
        ["EUR", "HUF"],
    )

    assert converted == {}


def test_convert_prices_skips_native_currency(monkeypatch):
    calls = []

    def fake_fetch_exchange_rate(from_currency, to_currency, year, month):
        calls.append((from_currency, to_currency))
        return 350.0

    monkeypatch.setattr(fetch_prices, "fetch_exchange_rate", fake_fetch_exchange_rate)

    converted = fetch_prices.convert_prices(
        Ticker("VWCE.DE", 10.0, "EUR", "2024-01-02"),
        2024,
        1,
        ["EUR", "HUF"],
    )

    assert converted == {"HUF": 3500.0}
    assert calls == [("EUR", "HUF")]


def test_fetch_exchange_rate_returns_none_when_price_fetch_fails(monkeypatch, capsys):
    monkeypatch.setattr(
        fetch_prices,
        "fetch_first_day_of_month_price",
        lambda ticker, year, month: None,
    )

    rate = fetch_prices.fetch_exchange_rate("EUR", "HUF", 2024, 1)

    assert rate is None
    assert "Error fetching exchange rate EUR to HUF" in capsys.readouterr().out


def test_fetch_price_main_prints_json(monkeypatch, capsys):
    monkeypatch.setattr(fetch_price.yfinance, "set_tz_cache_location", lambda cache: None)
    monkeypatch.setattr(
        fetch_price,
        "fetch_first_day_of_month_price",
        lambda ticker, year, month: Ticker(ticker, 99.12, "EUR", "2024-01-02"),
    )

    result = fetch_price.main(
        SimpleNamespace(
            ticker="VWCE.DE",
            year=2024,
            month=1,
            cache=".yfinance-cache/",
            beancount=False,
            json=True,
        )
    )

    assert result is None
    assert json.loads(capsys.readouterr().out) == {
        "name": "VWCE.DE",
        "price": 99.12,
        "currency": "EUR",
        "date": "2024-01-02",
    }


def test_fetch_prices_main_prints_native_and_converted_prices_once(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        fetch_prices,
        "parse_commodities",
        lambda path: [Commodity(symbol="VWCE", ticker="VWCE.DE")],
    )
    monkeypatch.setattr(
        fetch_prices,
        "fetch_stock_price",
        lambda ticker, year, month: Ticker(ticker, 10.0, "EUR", "2024-01-02"),
    )
    monkeypatch.setattr(
        fetch_prices,
        "convert_prices",
        lambda stock_data, year, month, target_currencies: {"HUF": 3500.0},
    )

    fetch_prices.main(
        SimpleNamespace(
            commodities="commodities.beancount",
            year=2024,
            month=1,
            target_currencies=["EUR", "HUF"],
        )
    )

    assert capsys.readouterr().out.splitlines() == [
        "2024-01-02 price VWCE   10.00 EUR",
        "2024-01-02 price VWCE   3500.00 HUF",
    ]
