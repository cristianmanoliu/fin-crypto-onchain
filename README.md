# fin-crypto-onchain

Fundamental signals from on-chain metrics: NVT ratio, active addresses,
hash rate. A different signal class from price-based momentum or carry.

## Origin

Research idea #5 from `fin-crypto-lab` (2026-09-19). Lowest priority of the
five ideas. Requires a new data source and pipeline.

## What we know

- On-chain metrics are fundamentally different from price-based signals. They
  measure network usage, not market price patterns.
- Key metrics: NVT ratio (network value to transactions, analogous to P/E),
  active addresses (demand proxy), hash rate (security/miner conviction).
- Data sources: Glassnode (paid API), CoinMetrics (community tier available),
  or free alternatives.
- Coverage is limited to proof-of-work chains (BTC, LTC, etc.) for hash
  rate. Active addresses and NVT are broader.

## Why it's low priority

1. New data dependency. Every other idea reuses existing Kraken data.
2. Unclear API access. Free tiers may have rate limits or limited history.
3. Smaller universe. On-chain data is available for maybe 20-30 coins, vs
   99+ Kraken pairs.
4. Academic support is thinner than for momentum or carry.

## Progress

### Phase 0: Data access audit (DONE)

CoinMetrics community API (`community-api.coinmetrics.io/v4`) provides
everything we need. No API key required.

- **Rate limit:** 10 requests per 6 seconds per IP.
- **Active addresses (AdrActCnt):** 138 assets, daily, back to genesis.
- **Hash rate (HashRate):** 12 PoW assets (BTC, ETH, LTC, BCH, DOGE, etc.).
- **Market cap (CapMrktCurUSD):** available, back to 2010 for BTC.
- **Transfer count (TxTfrCnt):** available. NVT is not a pre-built metric,
  but we compute it as market_cap / smoothed_transfer_count.
- **PriceUSD:** available for returns.
- Glassnode was not needed. CoinMetrics community tier is sufficient.

### Phase 1: Single-factor tests (DONE, results below)

Tested three signals on BTC and ETH: NVT ratio (28d smoothed), active
address momentum (14d/90d MA crossover), and hash ribbon (30d/60d MA
crossover). Median split long/short, 7-day forward returns.

| Asset | Signal      | IS Spread (bp) | drop-top-5% | Tail carried? | OOS Spread (bp) |
|-------|-------------|-----------------|-------------|---------------|-----------------|
| BTC   | nvt         | +274            | +0.00       | No            | +187            |
| BTC   | addr_mom    | +143            | -0.01       | **YES**       | +230            |
| BTC   | hash_ribbon | +168            | -0.00       | **YES**       | +57             |
| ETH   | nvt         | +284            | -0.01       | **YES**       | +243            |
| ETH   | addr_mom    | +431            | -0.00       | **YES**       | -80             |

**Verdict:** BTC NVT is the only signal that passes the honesty battery
(positive drop-top-5%, not tail-carried). Its OOS spread (+187 bp/wk) is
directionally consistent with in-sample (+274 bp/wk), though magnitude
decayed. All other signals are tail-carried.

### Phase 2: Integration (DONE, negative result)

Tested BTC NVT as a timing overlay: go long BTC when NVT is below its
rolling 180-day median, flat otherwise.

| Period     | Buy-and-hold | NVT-timed | Timing value (bp/day) |
|------------|--------------|-----------|----------------------|
| In-sample  | +14861%      | -63%      | -24.1                |
| OOS        | +33%         | -2%       | -4.9                 |

**Verdict: KILL.** NVT timing destroys value. The Phase 1 median-split
spread was real but economically useless: sitting out when NVT is high
means missing BTC's strongest rallies. The opportunity cost overwhelms
any signal. Timing value is negative in both samples and fails every
honesty check (0/9 and 0/3 positive years).

## Final verdict

No tradeable signal survives. Three of five signals are tail-carried in
Phase 1. The one survivor (BTC NVT) fails as a timing overlay in Phase 2.
This confirms the README's original assessment: on-chain metrics are the
lowest priority idea for good reason.

## Honesty method

Same battery as `fin-crypto-lab`. Additional concern: on-chain data may have
look-ahead bias if the metric is published with a delay (e.g., NVT uses
transaction volume that settles T+1). Must verify data availability timing
before backtesting.

## Key risk

**Data quality.** On-chain metrics are computed by third-party providers with
varying methodologies. "Active addresses" can be gamed by wash activity.
NVT depends on the provider's transaction volume methodology. Different
providers may give different results for the same metric on the same chain.
