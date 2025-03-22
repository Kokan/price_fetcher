import pytest
from pandas import Timestamp

from fetch_price import fetch_first_day_of_month_price

def test_fetch_first_day_of_month_price_real_api():
    ticker = "VWCE.DE"
    year = 2024
    month = 1

    result = fetch_first_day_of_month_price(ticker, year, month)

    assert result is not None, "API call failed or no data available."
    assert isinstance(result["price"], float), "Price is not a valid float."
    assert result["price"] > 0, "Price should be greater than zero."
    assert isinstance(result["date"], str), "Date is not a str."
    assert result["date"] == '2024-01-02 00:00:00', "Date is not the first trading day of the month."

