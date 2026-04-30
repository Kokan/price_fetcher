from datetime import date

import store_prices
from fetch_prices import Commodity
from ticker import Ticker


def test_upsert_price_lines_replaces_existing_date_currency(tmp_path):
    prices_file = tmp_path / "VWCE.beancount"
    prices_file.write_text(
        "\n".join(
            [
                "2026-04-29 price VWCE   143.00 EUR",
                "2026-04-30 price VWCE   144.00 EUR",
            ]
        )
        + "\n"
    )

    store_prices.upsert_price_lines(
        prices_file,
        [
            "2026-04-30 price VWCE                     145.00 EUR",
            "2026-04-30 price VWCE                   55500.00 HUF",
        ],
    )

    assert prices_file.read_text().splitlines() == [
        "2026-04-29 price VWCE   143.00 EUR",
        "2026-04-30 price VWCE                     145.00 EUR",
        "2026-04-30 price VWCE                   55500.00 HUF",
    ]


def test_upsert_price_lines_preserves_existing_line_when_amount_is_same(tmp_path):
    prices_file = tmp_path / "VWCE.beancount"
    prices_file.write_text("2026-04-30 price VWCE\t145.00 EUR\n")

    store_prices.upsert_price_lines(
        prices_file,
        ["2026-04-30 price VWCE                     145.00 EUR"],
    )

    assert prices_file.read_text() == "2026-04-30 price VWCE\t145.00 EUR\n"


def test_store_commodity_prices_writes_year_file_and_main(tmp_path):
    store_prices.store_commodity_prices(
        tmp_path,
        Commodity(symbol="VWCE", ticker="VWCE.DE"),
        [
            "2026-04-30 price VWCE                     145.00 EUR",
            "2026-04-30 price VWCE                   55500.00 HUF",
        ],
    )

    assert (tmp_path / "2026" / "VWCE.beancount").read_text().splitlines() == [
        "2026-04-30 price VWCE                     145.00 EUR",
        "2026-04-30 price VWCE                   55500.00 HUF",
    ]
    assert (tmp_path / "2026" / "main.beancount").read_text() == (
        'include "VWCE.beancount"\n'
    )


def test_fetch_and_store_prices_writes_fetched_prices(monkeypatch, tmp_path):
    commodities_file = tmp_path / "commodities.beancount"
    commodities_file.write_text(
        """
2023-07-01 commodity VWCE
  ticker: "VWCE.DE"
""".strip()
    )

    monkeypatch.setattr(
        store_prices,
        "fetch_price_for_date",
        lambda ticker, price_date: Ticker(ticker, 145.0, "EUR", "2026-04-30"),
    )
    monkeypatch.setattr(
        store_prices,
        "convert_prices_for_date",
        lambda stock_data, price_date, target_currencies: {"HUF": 55500.0},
    )

    stored_count = store_prices.fetch_and_store_prices(
        commodities_file,
        tmp_path,
        date(2026, 4, 30),
        ["EUR", "HUF"],
        [],
    )

    assert stored_count == 1
    assert (tmp_path / "2026" / "VWCE.beancount").read_text().splitlines() == [
        "2026-04-30 price VWCE                     145.00 EUR",
        "2026-04-30 price VWCE                   55500.00 HUF",
    ]


def test_currency_pair_price_lines_include_fetched_direction():
    lines_by_symbol = store_prices.currency_pair_price_lines(
        "EUR",
        "HUF",
        Ticker("EURHUF=X", 400.0, "HUF", "2026-04-30"),
    )

    assert lines_by_symbol == {
        "EUR": ["2026-04-30 price EUR                400.00000000 HUF"],
    }


def test_fetch_and_store_prices_writes_currency_rates(monkeypatch, tmp_path):
    commodities_file = tmp_path / "commodities.beancount"
    commodities_file.write_text(
        """
2023-07-01 commodity VWCE
  ticker: "VWCE.DE"
""".strip()
    )

    def fake_fetch_price_for_date(ticker, price_date):
        prices = {
            "VWCE.DE": Ticker("VWCE.DE", 145.0, "EUR", "2026-04-30"),
            "EURHUF=X": Ticker("EURHUF=X", 400.0, "HUF", "2026-04-30"),
        }
        return prices[ticker]

    monkeypatch.setattr(
        store_prices,
        "fetch_price_for_date",
        fake_fetch_price_for_date,
    )
    monkeypatch.setattr(
        store_prices,
        "convert_prices_for_date",
        lambda stock_data, price_date, target_currencies: {},
    )

    stored_count = store_prices.fetch_and_store_prices(
        commodities_file,
        tmp_path,
        date(2026, 4, 30),
        ["EUR", "HUF"],
        [("EUR", "HUF")],
    )

    assert stored_count == 2
    assert (tmp_path / "2026" / "EUR.beancount").read_text() == (
        "2026-04-30 price EUR                400.00000000 HUF\n"
    )
    assert (tmp_path / "2026" / "main.beancount").read_text().splitlines() == [
        'include "EUR.beancount"',
        'include "VWCE.beancount"',
    ]


def test_format_existing_price_line_aligns_price_columns():
    assert store_prices.format_existing_price_line(
        "2024-01-02 price VWCE\t(107.04*382.11) HUF"
    ) == "2024-01-02 price VWCE            (107.04*382.11) HUF"
