"""
Filter tests (approved by Muhammad Ali, 2026-10-02). Signals are filtered BEFORE
the one-trade-at-a-time simulation, so each filter changes which trades happen.
 F1 TREND : ADX(14) on the signal candle >= 25 (trending market only).
 F2 S/R   : TradingLab's own "part 2" - price must be AT a support (longs) /
            resistance (shorts) that has already been tested at least twice.
            Objective version: swing lows/highs = 5-bar fractals (confirmed 2
            bars later, no look-ahead) within the last 150 candles. A level is
            "tested twice" if two or more swing points sit within 0.5 x ATR of
            each other. The signal candle or one of the 5 before it must have
            touched that level (low within 0.5 x ATR of it) and the close must
            still be above it (longs) / below it (shorts).
 F3 STOP  : distance from close to the 200 MA (= the stop) is at least 1 x ATR,
            so the spread cannot eat a tiny stop.
Same costs and walking as macd.py. 200 EMA, 1.5R target.
"""
import numpy as np, pandas as pd
from macd import load_m1, bars, indicators, signals, run, summary


def sr_ok(b, lookback=150, tol=0.5):
    h, l, c, a = b.h.to_numpy(), b.l.to_numpy(), b.c.to_numpy(), b.atr.to_numpy()
    n = len(b)
    piv_lo = np.zeros(n, bool); piv_hi = np.zeros(n, bool)
    for i in range(2, n - 2):
        piv_lo[i] = l[i] < l[i-1] and l[i] < l[i-2] and l[i] < l[i+1] and l[i] < l[i+2]
        piv_hi[i] = h[i] > h[i-1] and h[i] > h[i-2] and h[i] > h[i+1] and h[i] > h[i+2]
    sup = np.zeros(n, bool); res = np.zeros(n, bool)
    for k in range(lookback, n):
        lo_idx = np.flatnonzero(piv_lo[k - lookback:k - 2]) + k - lookback   # confirmed pivots only
        hi_idx = np.flatnonzero(piv_hi[k - lookback:k - 2]) + k - lookback
        t = tol * a[k]
        recent_lo = l[k - 5:k + 1].min(); recent_hi = h[k - 5:k + 1].max()
        lv = l[lo_idx]
        for v in lv:
            if (np.abs(lv - v) <= t).sum() >= 2 and recent_lo <= v + t and c[k] > v:
                sup[k] = True; break
        hv = h[hi_idx]
        for v in hv:
            if (np.abs(hv - v) <= t).sum() >= 2 and recent_hi >= v - t and c[k] < v:
                res[k] = True; break
    return sup, res


if __name__ == "__main__":
    m1 = load_m1()
    rows, keep = [], []
    for tf, name in [(15, "M15"), (60, "H1"), (240, "H4")]:
        b = indicators(bars(m1, tf), "EMA")
        s0 = signals(b)
        sup, res = sr_ok(b)
        f = {
            "original": np.ones(len(b), bool),
            "F1_trend": (b.adx >= 25).to_numpy(),
            "F2_sr": np.where(s0 == 1, sup, res),
            "F3_minstop": ((b.c - b.ma).abs() >= b.atr).to_numpy(),
        }
        f["F1+F3"] = f["F1_trend"] & f["F3_minstop"]
        f["F2+F3"] = f["F2_sr"] & f["F3_minstop"]
        for fname, m in f.items():
            s = s0.where(m, 0)
            for sm in ["real", "fixed:0.20"]:
                t = run(m1, b, s, 1.5, sm)
                r = dict(tf=name, filter=fname, spread=sm, **summary(t))
                for per, q in [("IS", t.entry_ts.dt.year <= 2023), ("OOS", t.entry_ts.dt.year >= 2024)] if len(t) else []:
                    ss = summary(t[q]); r[f"{per}_n"] = ss.get("trades"); r[f"{per}_win"] = ss.get("win_rate"); r[f"{per}_avgR"] = ss.get("avg_R")
                rows.append(r); print(r, flush=True)
                if len(t): keep.append(t.assign(tf=name, filter=fname, spread=sm))
    pd.DataFrame(rows).to_csv("filters.csv", index=False)
    pd.concat(keep).to_csv("trades_filters.csv.gz", index=False)
