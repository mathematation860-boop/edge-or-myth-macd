"""Sweep: timeframe x MA type x spread mode. Writes stats.csv + trades_all.csv.gz"""
import pandas as pd
from macd import load_m1, bars, indicators, signals, run, summary

m1 = load_m1()
print("M1 rows", len(m1), m1.ts.iloc[0], m1.ts.iloc[-1])
rows, alltr = [], []
for tf, name in [(15, "M15"), (60, "H1"), (240, "H4")]:
    b0 = bars(m1, tf)
    for ma in ["EMA", "SMA"]:
        b = indicators(b0.copy(), ma)
        s = signals(b)
        for sm in ["real", "zero", "fixed:0.20", "fixed:0.40"]:
            t = run(m1, b, s, 1.5, sm)
            r = dict(tf=name, ma=ma, spread=sm, signals=int((s != 0).sum()), **summary(t))
            for per, q in [("IS_2020_23", t.entry_ts.dt.year <= 2023), ("OOS_2024_26", t.entry_ts.dt.year >= 2024)]:
                ss = summary(t[q]) if len(t) else {}
                r[f"{per}_win"] = ss.get("win_rate"); r[f"{per}_avgR"] = ss.get("avg_R"); r[f"{per}_n"] = ss.get("trades")
            for lab, q in [("trend_adx25", t.adx >= 25), ("side_adx25", t.adx < 25)] if len(t) else []:
                ss = summary(t[q]); r[f"{lab}_win"] = ss.get("win_rate"); r[f"{lab}_avgR"] = ss.get("avg_R"); r[f"{lab}_n"] = ss.get("trades")
            rows.append(r); print(r, flush=True)
            if len(t):
                t = t.assign(tf=name, ma=ma, spread=sm); alltr.append(t)
pd.DataFrame(rows).to_csv("stats.csv", index=False)
pd.concat(alltr).to_csv("trades_all.csv.gz", index=False)
