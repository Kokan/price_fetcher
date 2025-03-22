from dataclasses import dataclass, asdict
import json


@dataclass
class Ticker:
    name: str
    price: float
    currency: str
    date: str


def format_json(ticker: Ticker) -> str:
    return json.dumps(asdict(ticker))


def format_beancount(ticker: Ticker) -> str:
    # 2023-01-02 price VWCE	92.26 EUR
    return f"{ticker.date} price {ticker.name}\t{ticker.price} {ticker.currency}"


def format_text(ticker: Ticker) -> str:
    return f"Ticker: {ticker.name} Price: {ticker.price} Date: {ticker.date}"
