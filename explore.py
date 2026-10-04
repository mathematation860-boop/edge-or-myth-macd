"""Extra checks after the filter run: (a) stricter S/R version, (b) long vs short
split of the best-looking filters, to see whether 2024-26 gains are just the gold bull run."""
import numpy as np, pandas as pd
from macd import load_m1, bars, indicators, signals, run, summary
from filt import sr_ok
class filt_sr: sr_ok = staticmethod(sr_ok)
m1 = load_m1(); rows=[]
for tf, name in [(15,"M15"),(60,"H1"),(240,"H4")]:
    b = indicators(bars(m1, tf), "EMA"); s0 = signals(b)
    sup, res = filt_sr.sr_ok(b, tol=0.2)
    m = np.where(s0==1, sup, res)
    t = run(m1, b, s0.where(m,0), 1.5, "real")
    r=dict(tf=name, test="F2_sr_strict(0.2ATR)", passed=int((s0.where(m,0)!=0).sum()), **summary(t))
    for per,q in [("IS",t.entry_ts.dt.year<=2023),("OOS",t.entry_ts.dt.year>=2024)]:
        ss=summary(t[q]); r[per+"_n"]=ss.get("trades"); r[per+"_avgR"]=ss.get("avg_R")
    rows.append(r); print(r, flush=True)
d=pd.read_csv("trades_filters.csv.gz", parse_dates=["entry_ts"])
for (tf,f) in [("H1","F1+F3"),("H1","F1_trend"),("H4","F3_minstop"),("H1","original")]:
    q=d[(d.tf==tf)&(d["filter"]==f)&(d.spread=="real")]
    for side in ["LONG","SHORT"]:
        for per,p in [("IS",q.entry_ts.dt.year<=2023),("OOS",q.entry_ts.dt.year>=2024)]:
            z=q[(q.side==side)&p]; rows.append(dict(tf=tf,test=f"{f} {side} {per}",trades=len(z),win_rate=round(100*(z.R>0).mean(),1) if len(z) else None,avg_R=round(z.R.mean(),3) if len(z) else None))
pd.DataFrame(rows).to_csv("explore.csv",index=False)
print(pd.DataFrame(rows).to_string())
