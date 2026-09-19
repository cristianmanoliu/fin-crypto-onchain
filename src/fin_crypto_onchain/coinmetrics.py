"""CoinMetrics community API client.
Run: uv run python -m fin_crypto_onchain.coinmetrics btc"""
import sys
import time

import httpx
import polars as pl

from fin_crypto_onchain import config

RATE_LIMIT_S = 0.7
PAGE_SIZE = 10_000


def get_asset_metrics(asset: str, start: str, end: str,
                      metrics: list[str] | None = None) -> pl.DataFrame:
    metrics = metrics or config.METRICS
    url = f"{config.COINMETRICS_BASE}/timeseries/asset-metrics"
    frames: list[pl.DataFrame] = []
    params = {
        "assets": asset,
        "metrics": ",".join(metrics),
        "frequency": "1d",
        "start_time": start,
        "end_time": end,
        "page_size": PAGE_SIZE,
    }

    with httpx.Client(timeout=30) as client:
        while True:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            body = resp.json()
            rows = body.get("data", [])
            if not rows:
                break
            frames.append(pl.DataFrame(rows))
            next_url = body.get("next_page_url")
            if not next_url:
                break
            url = next_url
            params = {}
            time.sleep(RATE_LIMIT_S)

    if not frames:
        return pl.DataFrame()
    df = pl.concat(frames)
    df = df.with_columns(pl.col("time").str.slice(0, 10).str.to_date().alias("date"))
    numeric_cols = [c for c in df.columns if c not in ("asset", "time", "date")]
    df = df.with_columns([pl.col(c).cast(pl.Float64) for c in numeric_cols])
    return df.select(["date", "asset"] + numeric_cols).sort("date")


if __name__ == "__main__":
    asset = sys.argv[1] if len(sys.argv) > 1 else "btc"
    df = get_asset_metrics(asset, "2020-01-01", "2020-01-10")
    print(df)
