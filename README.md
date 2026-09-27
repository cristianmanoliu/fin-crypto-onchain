# fin-crypto-onchain

This project tests on-chain signals for crypto assets. On-chain metrics measure network use, not price patterns. They are a different signal class from momentum or carry.

## Data source

The CoinMetrics community API (`community-api.coinmetrics.io/v4`) provides all necessary data. No API key is necessary.

- Rate limit: 10 API calls for each 6 seconds, for each IP address.
- Active addresses (AdrActCnt): 138 assets, daily, back to genesis.
- Hash rate (HashRate): 12 proof-of-work (PoW) assets (BTC, ETH, LTC, BCH, DOGE, and others).
- Market cap (CapMrktCurUSD): available for BTC back to 2010.
- Transaction count (TxTfrCnt): available. NVT is not a pre-built metric. The project calculates it as market cap divided by smooth transaction count.
- PriceUSD: available for price returns.

## Phase 1: Single-factor tests (DONE)

The project tested three signals on BTC and ETH: NVT ratio (28-day smooth), active address momentum (14d/90d MA crossover), and hash ribbon (30d/60d MA crossover). The test used a median-split long/short with 7-day forward price returns.

| Asset | Signal      | IS Spread (bp) | drop-top-5% | Tail carried? | OOS Spread (bp) |
|-------|-------------|-----------------|-------------|---------------|-----------------|
| BTC   | nvt         | +274            | +0.00       | No            | +187            |
| BTC   | addr_mom    | +143            | -0.01       | YES           | +230            |
| BTC   | hash_ribbon | +168            | -0.00       | YES           | +57             |
| ETH   | nvt         | +284            | -0.01       | YES           | +243            |
| ETH   | addr_mom    | +431            | -0.00       | YES           | -80             |

BTC NVT is the only signal that passes the honesty battery. It has a positive drop-top-5% and is not tail-carried. Its OOS spread (+187 bp/wk) agrees with the in-sample spread (+274 bp/wk) in direction, but the magnitude decreased. All other signals are tail-carried.

## Phase 2: Integration (DONE, negative result)

The project tested BTC NVT as a time overlay: go long BTC when NVT is below its rolling 180-day median, and flat if NVT is not below the median.

| Period     | Buy-and-hold | NVT-timed | Timing value (bp/day) |
|------------|--------------|-----------|----------------------|
| In-sample  | +14861%      | -63%      | -24.1                |
| OOS        | +33%         | -2%       | -4.9                 |

The NVT time overlay destroys value. The Phase 1 median-split spread was a correct spread, but it is economically useless. Sitting out when NVT is high means missing BTC's strongest rallies. The cost of that missed exposure exceeds the signal value. The timing value is negative in the two samples and is unsatisfactory for all honesty checks (0/9 positive years in-sample, 0/3 OOS).

## Verdict: KILL

No tradeable signal survives. Three of the five signals are tail-carried in Phase 1. The one survivor (BTC NVT) is unsatisfactory as a time overlay in Phase 2.

## Honesty method

The project uses the same battery as `fin-crypto-lab`.

Caution: On-chain data can have look-ahead bias if the provider makes the metric available after a lag. For example, NVT uses transaction volume that settles T+1. Make sure that data availability timing is correct before backtesting.

## Data quality risk

Third-party providers calculate on-chain metrics with different methodologies. The term "active addresses" can show wash trading work. NVT depends on the provider's transaction volume methodology. Different providers can give different results for the same metric on the same chain.
