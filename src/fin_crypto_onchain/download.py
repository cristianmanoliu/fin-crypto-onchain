"""Download on-chain metrics from CoinMetrics community API.
Run: uv run python -m fin_crypto_onchain.download"""
import logging
import sys
import time

from fin_crypto_onchain import config
from fin_crypto_onchain.coinmetrics import get_asset_metrics, RATE_LIMIT_S

log = logging.getLogger(__name__)


def download_all() -> int:
    assets = config.ASSETS_TIER1 + config.ASSETS_TIER2
    start = config.FORM_START.isoformat()
    end = config.FORM_END.isoformat()
    data_dir = config.DATA_DIR / "metrics"
    data_dir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for i, asset in enumerate(assets, 1):
        log.info("[%d/%d] %s", i, len(assets), asset)
        try:
            df = get_asset_metrics(asset, start, end)
            if df.is_empty():
                log.warning("%s: no data", asset)
                continue
            path = data_dir / f"{asset}.parquet"
            df.write_parquet(path)
            log.info("%s: %d days (%s to %s)", asset, df.height,
                     df["date"][0], df["date"][-1])
        except Exception:
            log.exception("FAILED: %s", asset)
            errors += 1
        time.sleep(RATE_LIMIT_S)
    return errors


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    errors = download_all()
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
