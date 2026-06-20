# TODO: switch back to akshare library once proxy is stable
# Currently using East Money + Yahoo Finance fallback, turnover_rate may be 0.0

import sys
import os
import json
import requests
from datetime import datetime

# add project root to path so we can import from contracts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts import source_schema

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EM_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_em_secid(stock_code):
    # Purpose: convert a stock code to East Money secid format (market prefix + code)
    # Input: stock_code (string) e.g. "000001" or "600000"
    # Output: (string) secid e.g. "0.000001" for Shenzhen, "1.600000" for Shanghai

    if stock_code.startswith("6"):
        return "1." + stock_code
    else:
        return "0." + stock_code


def get_yahoo_suffix(stock_code):
    # Purpose: convert a stock code to Yahoo Finance ticker format
    # Input: stock_code (string) e.g. "000001" or "600000"
    # Output: (string) ticker e.g. "000001.SZ" or "600000.SS"

    if stock_code.startswith("6"):
        return stock_code + ".SS"
    else:
        return stock_code + ".SZ"


def fetch_from_eastmoney(stock_code):
    # Purpose: try to get price and turnover rate from East Money API
    # Input: stock_code (string)
    # Output: (dict) with close_price and turnover_rate, or None if request fails

    params = {
        "fltt": "2",
        "invt": "2",
        "secids": get_em_secid(stock_code),
        "fields": "f12,f2,f8"  # f12=code, f2=price, f8=turnover_rate
    }

    try:
        r = requests.get(EM_URL, params=params, headers=HEADERS, timeout=8)
    except requests.exceptions.RequestException:
        return None

    if r.status_code != 200:
        return None

    try:
        body = r.json()
        diff = body["data"]["diff"]
        if len(diff) == 0:
            return None
        row = diff[0]
        return {
            "close_price": float(row["f2"]),
            "turnover_rate": float(row["f8"])
        }
    except (KeyError, ValueError, TypeError):
        return None


def fetch_from_yahoo(stock_code):
    # Purpose: fall back to Yahoo Finance for price when East Money is unavailable
    # Input: stock_code (string)
    # Output: (dict) with close_price and turnover_rate (0.0 if unavailable), or None if fails

    ticker = get_yahoo_suffix(stock_code)
    url = YAHOO_URL + ticker

    try:
        r = requests.get(url, params={"interval": "1d", "range": "1d"}, headers=HEADERS, timeout=10)
    except requests.exceptions.RequestException:
        return None

    if r.status_code != 200:
        return None

    try:
        meta = r.json()["chart"]["result"][0]["meta"]
        close_price = float(meta["regularMarketPrice"])
        return {
            "close_price": close_price,
            "turnover_rate": 0.0  # not available from Yahoo Finance for A-shares
        }
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def fetch(stock_code):
    # Purpose: get today's close price and turnover rate for one A-share stock, write to data/
    # Input: stock_code (string) - A-share stock code, e.g. "000001"
    # Output: none (writes to data/source_akshare.json)

    market_data = fetch_from_eastmoney(stock_code)

    if market_data is not None:
        print("source_akshare: fetched from East Money")
    else:
        print("source_akshare: East Money unavailable, trying Yahoo Finance")
        market_data = fetch_from_yahoo(stock_code)

    if market_data is None:
        print("source_akshare: all data sources failed for stock:", stock_code)
        return

    close_price = market_data["close_price"]
    turnover_rate = market_data["turnover_rate"]

    text = (
        "Stock " + stock_code +
        " closed at " + str(close_price) +
        " with turnover rate " + str(turnover_rate) + "%"
    )

    data = {
        "source_name": "akshare",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "items": [
            {
                "text": text,
                "meta": {
                    "stock_code": stock_code,
                    "close_price": close_price,
                    "turnover_rate": turnover_rate
                }
            }
        ]
    }

    is_valid = source_schema.validate(data)
    if not is_valid:
        print("source_akshare: data failed validation, not writing file")
        return

    data_dir = os.path.join(PROJECT_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, "source_akshare.json")

    f = open(filepath, "w", encoding="utf-8")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.close()

    print("source_akshare: wrote ->", close_price, "/ turnover", turnover_rate, "%")


if __name__ == "__main__":
    fetch("000001")
