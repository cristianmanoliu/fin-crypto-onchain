"""Phase 2: test NVT as a timing overlay on BTC.
Run: uv run python -m fin_crypto_onchain.blend

Does NVT add value as a "go flat when NVT is high" filter?
Compare: always-long BTC vs NVT-timed (long only when NVT < median).
"""
import logging
import sys

import numpy as np
import polars as pl

from fin_crypto_onchain import config
from fin_crypto_onchain.signals import nvt_ratio
from fin_crypto_onchain.quant_honesty import honesty, format_report

log = logging.getLogger(__name__)


def run_blend() -> None:
    path = config.DATA_DIR / "metrics" / "btc.parquet"
    df = pl.read_parquet(path)
    df = nvt_ratio(df)
    df = df.with_columns(
        (pl.col("PriceUSD").shift(-1) / pl.col("PriceUSD") - 1.0).alias("daily_ret")
    )
    df = df.filter(pl.col("nvt").is_not_null() & pl.col("daily_ret").is_not_null())

    train = df.filter(pl.col("date") <= config.TRAIN_END)
    test = df.filter(pl.col("date") > config.TRAIN_END)

    for label, subset in [("IN-SAMPLE", train), ("OUT-OF-SAMPLE", test)]:
        if subset.height < 60:
            print(f"\n{label}: too few rows ({subset.height})")
            continue

        nvt_vals = subset["nvt"].to_numpy()
        rets = subset["daily_ret"].to_numpy()
        dates = subset["date"].to_numpy()

        # Rolling 180-day percentile rank. Point-in-time safe: only uses past data.
        lookback = 180
        pct_rank = np.full_like(nvt_vals, np.nan)
        for i in range(lookback, len(nvt_vals)):
            window = nvt_vals[i - lookback:i]
            pct_rank[i] = np.mean(window < nvt_vals[i])
        valid = np.isfinite(pct_rank)
        nvt_vals, rets, dates, pct_rank = (
            nvt_vals[valid], rets[valid], dates[valid], pct_rank[valid],
        )

        long_mask = pct_rank < 0.5
        timed_rets = np.where(long_mask, rets, 0.0)

        print(f"\n{'='*60}")
        print(f"  {label} ({dates[0]} to {dates[-1]})")
        print(f"{'='*60}")

        bh_cum = float(np.prod(1 + rets) - 1) * 100
        timed_cum = float(np.prod(1 + timed_rets) - 1) * 100
        pct_in = float(long_mask.mean()) * 100

        print(f"  Buy-and-hold cumulative: {bh_cum:+.1f}%")
        print(f"  NVT-timed cumulative:    {timed_cum:+.1f}%")
        print(f"  Time in market:          {pct_in:.0f}%")

        diff = timed_rets - rets
        years = dates.astype("datetime64[Y]").astype(int) + 1970
        by_year = {}
        for y in np.unique(years):
            by_year[int(y)] = diff[years == y].tolist()

        print(f"\n  Honesty on timing value (timed minus always-long):")
        h = honesty(diff * 1e4, by_year={k: [x * 1e4 for x in v] for k, v in by_year.items()})
        print(format_report(h, unit="bp"))


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    run_blend()
    return 0


if __name__ == "__main__":
    sys.exit(main())
