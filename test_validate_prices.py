import validate_prices


def test_validate_prices_accepts_generated_yearly_main(tmp_path):
    year_dir = tmp_path / "prices" / "2026"
    year_dir.mkdir(parents=True)
    (year_dir / "OTP.beancount").write_text(
        "\n".join(
            [
                "2026-04-30 price OTP   112.32 EUR",
                "2026-04-30 price OTP   41600.00 HUF",
            ]
        )
        + "\n"
    )
    (year_dir / "main.beancount").write_text('include "OTP.beancount"\n')
    (tmp_path / "prices" / "main.beancount").write_text(
        'include "2026/main.beancount"\n'
    )

    assert validate_prices.validate_prices(tmp_path / "prices") == 0


def test_validate_prices_reports_top_level_beancount_errors(tmp_path):
    prices_dir = tmp_path / "prices"
    prices_dir.mkdir()
    (prices_dir / "main.beancount").write_text("this is not beancount\n")

    assert validate_prices.validate_prices(prices_dir) > 0


def test_validate_prices_falls_back_to_yearly_main_files(tmp_path):
    year_dir = tmp_path / "prices" / "2026"
    year_dir.mkdir(parents=True)
    (year_dir / "main.beancount").write_text("this is not beancount\n")

    assert validate_prices.validate_prices(tmp_path / "prices") > 0
