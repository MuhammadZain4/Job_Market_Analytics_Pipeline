import requests
import re
from datetime import datetime

FX_CACHE = {}
FX_DATE = None

CURRENCIES_TO_FETCH = ["EUR", "GBP", "PKR", "INR", "CAD", "AUD", "CHF", "JPY", "CNY", "SGD", "NZD", "SEK", "NOK", "BRL", "MXN", "KRW", "TRY", "ZAR"]

USD_RATES = {
    "USD": 1.0, "EUR": 0.86, "GBP": 0.75, "PKR": 278.0, "INR": 83.0,
    "CAD": 1.36, "AUD": 1.50, "CHF": 0.89, "JPY": 150.0, "CNY": 7.20,
    "SGD": 1.33, "NZD": 1.62, "SEK": 10.40, "NOK": 10.50, "BRL": 4.95,
    "MXN": 17.0, "KRW": 1320.0, "TRY": 30.0, "ZAR": 18.50,
    "DKK": 6.0, "PLN": 4.0, "CZK": 22.0, "HUF": 350.0, "ILS": 3.60,
    "MYR": 4.60, "THB": 35.0, "PHP": 56.0, "IDR": 15500.0, "VND": 24500.0, "NGN": 1500.0,
}

def fetch_latest_rates():
    global FX_CACHE, FX_DATE
    FX_CACHE = dict(USD_RATES)
    FX_DATE = datetime.now().strftime("%Y-%m-%d")
    fetched = 0
    for curr in CURRENCIES_TO_FETCH:
        try:
            resp = requests.get(f"https://api.frankfurter.dev/v2/rate/USD/{curr}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                rate = data.get("rate")
                if rate and rate > 0:
                    FX_CACHE[curr] = rate
                    fetched += 1
        except Exception:
            pass
    print(f"[FX] Rates from Frankfurter API ({fetched}/{len(CURRENCIES_TO_FETCH)} fetched), date={FX_DATE}")

def convert_to_usd(amount, from_currency):
    if not amount or amount <= 0 or not from_currency:
        return None
    from_currency = from_currency.upper()
    if from_currency == "USD":
        return round(amount, 2)
    if from_currency in FX_CACHE:
        rate = FX_CACHE[from_currency]
        if rate > 0:
            result = round(amount / rate, 2)
            return result if result < 5_000_000 else None
    return None

def detect_currency(text):
    if not text:
        return None
    currency_map = {
        "$": "USD", "usd": "USD", "USD": "USD", "dollar": "USD",
        "\u20ac": "EUR", "eur": "EUR", "EUR": "EUR", "euro": "EUR",
        "\u00a3": "GBP", "gbp": "GBP", "GBP": "GBP", "pound": "GBP",
        "rs": "PKR", "PKR": "PKR", "pkr": "PKR", "rupee": "INR",
        "\u20b9": "INR", "inr": "INR", "INR": "INR",
        "\u00a5": "JPY", "jpy": "JPY", "JPY": "JPY", "cad": "CAD", "CAD": "CAD",
        "aed": "AED", "AED": "AED",
    }
    for pattern, curr in currency_map.items():
        if re.search(re.escape(pattern), text, re.IGNORECASE):
            return curr
    return None

def parse_salary_text(text):
    if not text:
        return None, None, None
    patterns = [
        (r'(?:USD|usd|\$)\s*([\d,]+)\s*(?:k|K)?\s*[--\u2013\u2014to]+\s*([\d,]+)\s*(?:k|K)?\s*', "USD"),
        (r'(?:EUR|eur|\u20ac)\s*([\d,]+)\s*(?:k|K)?\s*[--\u2013\u2014to]+\s*([\d,]+)\s*(?:k|K)?\s*', "EUR"),
        (r'(?:GBP|gbp|\u00a3)\s*([\d,]+)\s*(?:k|K)?\s*[--\u2013\u2014to]+\s*([\d,]+)\s*(?:k|K)?\s*', "GBP"),
        (r'(\$[\d,]+)\s*[--\u2013\u2014to]+\s*(\$[\d,]+)', "USD"),
    ]
    for pat, default_curr in patterns:
        m = re.search(pat, text)
        if m:
            g1 = m.group(1).replace(",", "").replace("$", "")
            min_val = float(g1)
            max_val = None
            if m.group(2):
                g2 = m.group(2).replace(",", "").replace("$", "")
                max_val = float(g2)
            return min_val, max_val, default_curr
    return None, None, None
