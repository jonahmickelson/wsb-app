# prices.py
import pandas as pd
import yfinance as yf

def fetch_price_table(tickers: list[str], days_back: int = 7) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame(columns=["date","ticker","close","ret1d"])

    data = yf.download(
        tickers = sorted(set(tickers)),
        period = f"{days_back}d",
        interval = "1d",
        auto_adjust = True,
        threads = True,
        progress = False,
        group_by = "ticker"
    )

    frames = []
    if isinstance(data.columns, pd.MultiIndex):
        for t in set(tickers):
            if (t, "Close") in data.columns:
                sub = data[(t, "Close")].rename("close").to_frame()
                sub["ticker"] = t
                frames.append(sub)
    else:
        sub = data.rename(columns={"Close":"close"})[["close"]].copy()
        if len(tickers) == 1:
            sub["ticker"] = tickers[0]
            frames.append(sub)

    if not frames:
        return pd.DataFrame(columns=["date","ticker","close","ret1d"])

    out = pd.concat(frames).reset_index()
    out = out.rename(columns={"Date":"date"})
    out["date"] = out["date"].dt.tz_localize(None).dt.date.astype(str)

    # ✅ explicitly disable forward filling to avoid warning
    out["ret1d"] = (
        out.sort_values(["ticker","date"])
           .groupby("ticker")["close"]
           .pct_change(fill_method=None)
           .mul(100)   # percent
           .round(2)
    )

    return out[["date","ticker","close","ret1d"]]
