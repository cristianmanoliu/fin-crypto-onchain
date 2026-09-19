import numpy as np
import polars as pl

from fin_crypto_onchain.signals import nvt_ratio, addr_momentum, hash_ribbon, add_returns


def _make_df(n=100):
    return pl.DataFrame({
        "date": pl.date_range(pl.date(2020, 1, 1), pl.date(2020, 1, 1) + (n - 1) * pl.duration(days=1), eager=True)[:n],
        "CapMrktCurUSD": np.linspace(1e9, 2e9, n),
        "TxTfrCnt": np.linspace(500_000, 600_000, n),
        "AdrActCnt": np.linspace(300_000, 400_000, n),
        "HashRate": np.linspace(1e8, 2e8, n),
        "PriceUSD": np.linspace(7000, 10000, n),
    })


def test_nvt_produces_column():
    df = nvt_ratio(_make_df())
    assert "nvt" in df.columns
    valid = df.filter(pl.col("nvt").is_not_null())
    assert valid.height > 0
    assert all(v > 0 for v in valid["nvt"].to_list())


def test_addr_momentum_centered():
    df = addr_momentum(_make_df(200), fast=14, slow=90)
    assert "addr_mom" in df.columns
    valid = df.filter(pl.col("addr_mom").is_not_null())
    assert valid.height > 0


def test_hash_ribbon():
    df = hash_ribbon(_make_df(200))
    assert "hash_ribbon" in df.columns


def test_add_returns_shift():
    df = add_returns(_make_df(), horizon=7)
    assert "fwd_ret_7d" in df.columns
    last_7 = df["fwd_ret_7d"][-7:]
    assert all(v is None for v in last_7.to_list())
