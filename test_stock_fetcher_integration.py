import pandas

import fetch_price
import fetch_prices
from ticker import Ticker


class FakeYFinanceTicker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.info = {"currency": "EUR"}


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


def test_convert_prices_skips_missing_exchange_rates(monkeypatch):
    def fake_fetch_exchange_rate(from_currency, to_currency, year, month):
        rates = {"EUR": 1.0, "HUF": None}
        return rates[to_currency]

    monkeypatch.setattr(fetch_prices, "fetch_exchange_rate", fake_fetch_exchange_rate)

    converted = fetch_prices.convert_prices(
        Ticker("VWCE.DE", 10.0, "EUR", "2024-01-02"),
        2024,
        1,
        ["EUR", "HUF"],
    )

    assert converted == {"EUR": 10.0}
