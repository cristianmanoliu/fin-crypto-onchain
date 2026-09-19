"""Single-factor on-chain signal study.
Run: uv run python -m fin_crypto_onchain.study

For each signal, splits the signal into quintiles each day and measures
the forward return spread (Q1 vs Q5). Then runs the honesty battery
on the long/short spread returns.

Phase 1 from the README: single-coin tests on BTC and ETH.
"""
import logging
import sys
from pathlib import Path

import numpy as np
import polars as pl

from fin_crypto_onchain import config
from fin_crypto_onchain.signals import (
    nvt_ratio, addr_momentum, hash_ribbon, add_returns,
)
from fin_crypto_onchain.quant_honesty import honesty, format_report

log = logging.getLogger(__name__)

HORIZON = 7

SIGNAL_FUNCS = {
    "nvt": nvt_ratio,
    "addr_mom": addr_momentum,
    "hash_ribbon": hash_ribbon,
}


def load_asset(asset: str) -> pl.DataFrame:
    path = config.DATA_DIR / "metrics" / f"{asset}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Run download first: {path}")
    return pl.read_parquet(path)


def single_factor_test(asset: str, signal_name: str,
                       train_end=config.TRAIN_END) -> dict:
    """Test one signal on one asset. Returns honesty dict plus metadata."""
    df = load_asset(asset)
    sig_func = SIGNAL_FUNCS[signal_name]
    df = sig_func(df)
    df = add_returns(df, HORIZON)

    ret_col = f"fwd_ret_{HORIZON}d"
    df = df.filter(
        pl.col(signal_name).is_not_null()
        & pl.col(ret_col).is_not_null()
        & pl.col(signal_name).is_finite()
        & pl.col(ret_col).is_finite()
    )

    in_sample = df.filter(pl.col("date") <= train_end)
    if in_sample.height < 60:
        log.warning("%s/%s: only %d rows in-sample, skipping",
                    asset, signal_name, in_sample.height)
        return {"asset": asset, "signal": signal_name, "n": in_sample.height,
                "skipped": True}

    sig = in_sample[signal_name].to_numpy()
    ret = in_sample[ret_col].to_numpy()

    if signal_name == "nvt":
        # ponytail: invert NVT so "low NVT = buy" maps to "high signal = buy"
        sig = -sig

    median_sig = np.median(sig)
    long_mask = sig > median_sig
    short_mask = sig <= median_sig

    long_ret = ret[long_mask]
    short_ret = ret[short_mask]
    spread = long_ret.mean() - short_ret.mean() if len(long_ret) and len(short_ret) else 0.0

    trade_returns = np.where(long_mask, ret, -ret)

    years = in_sample["date"].to_numpy().astype("datetime64[Y]").astype(int) + 1970
    by_year = {}
    for y in np.unique(years):
        by_year[int(y)] = trade_returns[years == y].tolist()

    h = honesty(trade_returns, by_year=by_year)
    h["asset"] = asset
    h["signal"] = signal_name
    h["spread_bp"] = spread * 1e4
    h["skipped"] = False

    oos = df.filter(pl.col("date") > train_end)
    if oos.height >= 30:
        oos_sig = oos[signal_name].to_numpy()
        oos_ret = oos[ret_col].to_numpy()
        if signal_name == "nvt":
            oos_sig = -oos_sig
        oos_median = np.median(oos_sig)
        oos_long = oos_ret[oos_sig > oos_median]
        oos_short = oos_ret[oos_sig <= oos_median]
        h["oos_spread_bp"] = (oos_long.mean() - oos_short.mean()) * 1e4 if len(oos_long) and len(oos_short) else float("nan")
        h["oos_n"] = oos.height
    else:
        h["oos_spread_bp"] = float("nan")
        h["oos_n"] = oos.height

    return h


def run_all() -> list[dict]:
    results = []
    for asset in config.ASSETS_TIER1:
        for sig_name in SIGNAL_FUNCS:
            if sig_name == "hash_ribbon" and asset == "eth":
                # ETH moved to PoS 2022-09, hash rate stops being meaningful
                log.info("Skipping hash_ribbon for eth (PoS transition)")
                continue
            log.info("Testing %s / %s", asset, sig_name)
            try:
                r = single_factor_test(asset, sig_name)
                results.append(r)
            except Exception:
                log.exception("FAILED: %s / %s", asset, sig_name)
    return results


def print_results(results: list[dict]) -> None:
    for r in results:
        print(f"\n{'='*60}")
        print(f"{r['asset'].upper()} / {r['signal']}")
        print(f"{'='*60}")
        if r.get("skipped"):
            print(f"  SKIPPED: only {r['n']} rows")
            continue
        print(f"  In-sample spread: {r['spread_bp']:+.1f} bp / {HORIZON}d")
        print(format_report(r, unit=""))
        if not np.isnan(r.get("oos_spread_bp", float("nan"))):
            print(f"  Out-of-sample spread: {r['oos_spread_bp']:+.1f} bp / {HORIZON}d (n={r['oos_n']})")
        else:
            print(f"  Out-of-sample: insufficient data (n={r.get('oos_n', 0)})")


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    results = run_all()
    print_results(results)

    config.RESULTS_DIR.mkdir(exist_ok=True)
    rows = [{k: v for k, v in r.items() if k != "by_year"} for r in results]
    pl.DataFrame(rows).write_parquet(config.RESULTS_DIR / "single_factor.parquet")
    log.info("Results saved to %s", config.RESULTS_DIR / "single_factor.parquet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
