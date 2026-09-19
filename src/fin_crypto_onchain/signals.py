"""On-chain signal generators. All operate on a single asset's DataFrame."""
import numpy as np
import polars as pl


def nvt_ratio(df: pl.DataFrame, window: int = 28) -> pl.DataFrame:
    """Network Value to Transactions ratio, smoothed over `window` days.
    NVT = market_cap / smoothed_transfer_count.
    Low NVT = network is cheap relative to usage (bullish).
    """
    smoothed_tx = pl.col("TxTfrCnt").rolling_mean(window_size=window)
    nvt = pl.col("CapMrktCurUSD") / smoothed_tx
    return df.with_columns(nvt.alias("nvt"))


def addr_momentum(df: pl.DataFrame, fast: int = 14,
                  slow: int = 90) -> pl.DataFrame:
    """Active address momentum: fast MA / slow MA - 1.
    Positive = accelerating network usage (bullish).
    """
    ma_fast = pl.col("AdrActCnt").rolling_mean(window_size=fast)
    ma_slow = pl.col("AdrActCnt").rolling_mean(window_size=slow)
    signal = ma_fast / ma_slow - 1.0
    return df.with_columns(signal.alias("addr_mom"))


def hash_ribbon(df: pl.DataFrame, fast: int = 30,
                slow: int = 60) -> pl.DataFrame:
    """Hash ribbon: fast MA of hash rate / slow MA - 1.
    Positive crossover after negative = miner capitulation ending (bullish).
    """
    ma_fast = pl.col("HashRate").rolling_mean(window_size=fast)
    ma_slow = pl.col("HashRate").rolling_mean(window_size=slow)
    signal = ma_fast / ma_slow - 1.0
    return df.with_columns(signal.alias("hash_ribbon"))


def add_returns(df: pl.DataFrame, horizon: int = 7) -> pl.DataFrame:
    """Forward returns over `horizon` days. Point-in-time safe:
    return on day t = price(t+horizon) / price(t) - 1."""
    fwd = pl.col("PriceUSD").shift(-horizon)
    ret = fwd / pl.col("PriceUSD") - 1.0
    return df.with_columns(ret.alias(f"fwd_ret_{horizon}d"))
