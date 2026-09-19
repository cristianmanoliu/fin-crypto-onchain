import datetime as dt
from pathlib import Path

DATA_DIR = Path("data")
RESULTS_DIR = Path("results")

COINMETRICS_BASE = "https://community-api.coinmetrics.io/v4"

METRICS = ["AdrActCnt", "HashRate", "CapMrktCurUSD", "TxTfrCnt", "PriceUSD"]

ASSETS_TIER1 = ["btc", "eth"]
ASSETS_TIER2 = ["ltc", "bch", "doge", "dash", "etc", "zec", "xmr", "bsv"]

FORM_START = dt.date(2015, 1, 1)
TRAIN_END = dt.date(2023, 12, 31)
FORM_END = dt.date(2026, 9, 18)
