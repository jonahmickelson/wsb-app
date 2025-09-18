# pipeline.py
import os
import pandas as pd
from scraper import collect_mentions_24h
from prices import fetch_price_table

BASE_DIR = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE_DIR, "data")
OUT_FILE = os.path.join(OUT_DIR, "mentions_history.csv")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    df_m = collect_mentions_24h()
    if df_m.empty:
        print("No mentions scraped.")
        return

    tickers = sorted(df_m["ticker"].unique().tolist())
    df_p = fetch_price_table(tickers, days_back=7)

    df = df_m.merge(df_p, on=["date", "ticker"], how="left")

    if os.path.exists(OUT_FILE):
        old = pd.read_csv(OUT_FILE)
        all_ = pd.concat([old, df]).drop_duplicates(subset=["date","ticker"], keep="last")
    else:
        all_ = df

    all_.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(all_)} total rows to {OUT_FILE}")

if __name__ == "__main__":
    main()