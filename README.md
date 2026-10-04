# Edge or Myth — "BEST MACD Trading Strategy [86% Win Rate]" tested on gold

Video: Edge or Myth on YouTube (@edgeormyth) — *I Fixed The 86% Win Rate MACD Strategy (Free TradingView Script)*
Source strategy: TradingLab, "BEST MACD Trading Strategy [86% Win Rate]" (youtu.be/rf_EQvubKlk, 4.5M views)

## The claim
MACD (12, 26, 9) + 200 moving average. Long when price is above the 200 MA and MACD crosses up **below** zero; short when price is below the 200 MA and MACD crosses down **above** zero. Stop at the 200 MA, target 1.5 × risk. Title claim: 86% win rate.

## Results on TradingView (XAUUSD 1H, OANDA, Jan 2025 – Oct 2026, $10,000, 1% risk per trade)
| | Original | Fixed (2 rules) |
|---|---|---|
| Trades | 111 | 30 |
| Win rate | 47.8% | 63.3% |
| Profit factor | 1.41 | 2.50 |
| Max drawdown | 7.78% | 2.82% |
| Net profit | +25.9% | +18.8% |

**The two rules** (both switchable in the script settings):
1. **Trend filter** — only trade when ADX(14) ≥ 25.
2. **Minimum stop** — the distance from price to the 200 EMA (the stop) must be at least 1 × ATR(14).

## Independent re-test (this repo): 6 years of Dukascopy data, real bid/ask spread
1-hour, 200 EMA, 1.5R, Jan 2020 – Sep 2026, real measured spread + $0.05 slippage per side, one trade at a time, trades walked on 1-minute bars (if stop and target are inside the same minute, the stop is assumed).

| Version | Trades | Win rate | Avg R | 2020–23 total | 2024–26 total |
|---|---|---|---|---|---|
| Original | 427 | 39.8% | −0.02 | −24.5R | +16.7R |
| Fixed (ADX ≥ 25 + stop ≥ 1 ATR) | 99 | 47.5% | +0.18 | −5.8R | +23.9R |

Honest notes:
- No version comes close to 86%. With a 1.5R target the breakeven win rate is 40%.
- In the choppy years (2020–2023) neither version made money; the fixed version lost about 4× less.
- From 2024 the fixed version averaged about +0.5R per trade — mostly longs during gold's uptrend. Treat it as a trend strategy.
- The original's own "part 2" (support/resistance + MACD) did not help in an objective test (see `filters.csv`, `F2_sr`).
- M15 loses heavily with real spreads (tiny stops); H4 has too few trades to judge.

## Files
- `MACD_200EMA_Gold_Fixed.pine` — the free TradingView strategy (Pine v5). Paste into Pine Editor → Add to chart.
- `macd.py` — rules, indicators, simulator (no look-ahead; closed candles only).
- `run.py` — sweep: M15/H1/H4 × EMA/SMA × spread (real, 0, 0.20, 0.40) → `stats.csv`, `trades_all.csv.gz`.
- `filt.py` — filter tests (trend, support/resistance, min stop, combos) → `filters.csv`, `trades_filters.csv.gz`.
- `explore.py` — stricter S/R version + long/short split by period → `explore.csv`.

Data: Dukascopy XAUUSD 1-minute bid/ask, 2020-01-01 → 2026-09-18 (same data as the earlier Edge or Myth repos).

Educational only — not financial advice.
