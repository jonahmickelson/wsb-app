# pipeline.py
import os
import pandas as pd
from datetime import datetime, timezone
from scraper import collect_mentions_24h   # rename if your function name differs
from prices import fetch_price_table

OUT_DIR = "data"
OUT_FILE = os.path.join(OUT_DIR, "mentions_history.csv")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) Scrape last 24h mentions → df_m (date, ticker, mentions, title?)
    df_m = collect_mentions_24h()
    if df_m.empty:
        print("No mentions scraped.")
        return

    # 2) Fetch recent prices for those tickers → df_p (date, ticker, close, ret1d %)
    tickers = sorted(df_m["ticker"].unique().tolist())
    df_p = fetch_price_table(tickers, days_back=7)

    # 3) Merge on (date, ticker)
    df = df_m.merge(df_p, on=["date", "ticker"], how="left")

    # 4) Append into history CSV (dedupe by date,ticker)
    if os.path.exists(OUT_FILE):
        old = pd.read_csv(OUT_FILE)
        all_ = pd.concat([old, df], ignore_index=True)
        all_ = all_.drop_duplicates(subset=["date","ticker"], keep="last")
    else:
        all_ = df

    all_.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(all_)} total rows to {OUT_FILE}")

if __name__ == "__main__":
    main()
