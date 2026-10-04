"""
TradingLab - "BEST MACD Trading Strategy [86% Win Rate]"
youtu.be/rf_EQvubKlk  (4.5M views)

His claim: "one of the highest win rate strategies you can possibly do",
"works in almost every single market", "it makes money", title: 86% win rate.

HIS RULES, MADE MECHANICAL (agreed with Muhammad Ali, 2026-10-02)
 Indicators: MACD (12, 26, 9) and a 200-period moving average
             (EMA is the main test, SMA checked as well).
 LONG : the signal candle CLOSES above the 200 MA, AND on that candle the
        MACD line crosses ABOVE the signal line, AND the cross happens
        BELOW the zero line (both lines < 0).
 SHORT: close below the 200 MA, MACD crosses BELOW the signal line, and the
        cross happens ABOVE the zero line (both lines > 0).
 ENTRY: open of the next candle (only closed candles are used - no look-ahead).
 STOP : the 200 MA value at the signal candle ("I set a stop loss below the
        200 day moving average ... it acts as a wall").
 TARGET: 1.5 x risk ("a 1.5 profit ratio").
 One trade at a time; a new signal while a trade is open is ignored.
 Timeframes: the video never says, so M15, H1 and H4 are all tested.
COSTS: real Dukascopy bid/ask. Longs buy the ask and sell the bid, shorts the
reverse; +$0.05 slippage per side. Trades are walked minute by minute on real
1-minute bars; if stop and target are both inside the same minute the STOP is
assumed (conservative - 1-minute is the finest data we have).
"""
import glob, numpy as np, pandas as pd

DATA = "/mnt/user-data/uploads/Gold-Trading-Assistant/data-dukascopy/bid_ask"
SLIP = 0.05


def load_m1():
    df = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(f"{DATA}/*.parquet")))
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["ts"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def bars(m1, tf):
    """Resample bid M1 into tf-minute bars (UTC). Keeps index of first/last minute."""
    key = m1.ts.dt.floor(f"{tf}min")
    g = m1.groupby(key)
    b = pd.DataFrame({"o": g.bid_open.first(), "h": g.bid_high.max(), "l": g.bid_low.min(),
                      "c": g.bid_close.last()})
    idx = m1.index.to_series().groupby(key)
    b["i0"] = idx.first().values
    b["i1"] = idx.last().values + 1          # first minute after the bar
    b = b[(b.i1 - b.i0) >= max(3, tf // 4)]  # drop near-empty bars (holiday stubs)
    b.index.name = "ts"
    return b.reset_index()


def ema(x, n): return x.ewm(span=n, adjust=False).mean()


def indicators(b, ma="EMA"):
    c = b.c
    macd = ema(c, 12) - ema(c, 26)
    sig = ema(macd, 9)
    b["macd"], b["sig"] = macd, sig
    b["ma"] = ema(c, 200) if ma == "EMA" else c.rolling(200).mean()
    # ADX(14) for regime labelling
    h, l = b.h, b.l
    up, dn = h.diff(), -l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    pdi = 100 * pd.Series(pdm).ewm(alpha=1 / 14, adjust=False).mean() / atr
    mdi = 100 * pd.Series(mdm).ewm(alpha=1 / 14, adjust=False).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    b["adx"] = dx.ewm(alpha=1 / 14, adjust=False).mean()
    b["atr"] = atr
    return b


def signals(b):
    up = (b.macd > b.sig) & (b.macd.shift() <= b.sig.shift())
    dn = (b.macd < b.sig) & (b.macd.shift() >= b.sig.shift())
    lng = up & (b.macd < 0) & (b.sig < 0) & (b.c > b.ma)
    sht = dn & (b.macd > 0) & (b.sig > 0) & (b.c < b.ma)
    s = pd.Series(0, index=b.index); s[lng] = 1; s[sht] = -1
    s[b.ma.isna()] = 0
    s.iloc[:300] = 0                          # indicator warm-up
    return s


def run(m1, b, sig, rr=1.5, spread_mode="real", maxbars=None):
    bo, bh, bl = m1.bid_open.to_numpy(), m1.bid_high.to_numpy(), m1.bid_low.to_numpy()
    spr_real = (m1.ask_close - m1.bid_close).to_numpy()
    if spread_mode == "real": sp, slip = spr_real, SLIP
    elif spread_mode == "zero": sp, slip = np.zeros(len(m1)), 0.0
    else: sp, slip = np.full(len(m1), float(spread_mode.split(":")[1])), 0.0
    out, busy_until = [], -1
    N = len(m1)
    for k in np.flatnonzero(sig.to_numpy() != 0):
        e = int(b.i1[k])                      # first minute after signal bar
        if e <= busy_until or e >= N - 1 or k + 1 >= len(b): continue
        side = int(sig[k]); stop = float(b.ma[k])
        entry = bo[e] + sp[e] + slip if side == 1 else bo[e] - slip
        risk = (entry - stop) * side
        if risk <= 0.05: continue             # price already through the MA - no valid stop
        tgt = entry + side * rr * risk
        res = None; m = e; CH = 20000
        while m < N and res is None:
            j = slice(m, min(N, m + CH))
            if side == 1:
                hs = np.flatnonzero(bl[j] <= stop); ht = np.flatnonzero(bh[j] >= tgt)
            else:
                hs = np.flatnonzero(bh[j] + sp[j] >= stop); ht = np.flatnonzero(bl[j] + sp[j] <= tgt)
            a = hs[0] if len(hs) else 10**9; t = ht[0] if len(ht) else 10**9
            if a < 10**9 or t < 10**9:
                if a <= t: res = ("STOP", m + a, stop - side * slip)
                else: res = ("TARGET", m + t, tgt - side * slip)
            m += CH
        if res is None: break                  # still open at the end of the data
        why, xi, xp = res
        R = side * (xp - entry) / risk
        busy_until = xi
        out.append(dict(side="LONG" if side == 1 else "SHORT", signal_ts=b.ts[k],
                        entry_ts=m1.ts[e], exit_ts=m1.ts[xi], entry=round(entry, 3),
                        stop=round(stop, 3), target=round(tgt, 3), exit=round(xp, 3),
                        risk=round(risk, 3), reward_planned=round(rr * risk, 3), R=R, reason=why,
                        adx=round(float(b.adx[k]), 1), atr=round(float(b.atr[k]), 3),
                        hours=round((xi - e) / 60, 1)))
    return pd.DataFrame(out)


def summary(t):
    if len(t) == 0: return dict(trades=0)
    w = (t.R > 0).mean(); eq = t.R.cumsum()
    return dict(trades=len(t), win_rate=round(100 * w, 1), avg_R=round(t.R.mean(), 3),
                total_R=round(t.R.sum(), 1), max_dd_R=round((eq.cummax() - eq).max(), 1),
                avg_risk_usd=round(t.risk.mean(), 2), med_hours=round(t.hours.median(), 1))
