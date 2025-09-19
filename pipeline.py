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

    # 1) Scrape mentions from Reddit
    df_m = collect_mentions_24h()
    if df_m.empty:
        print("No mentions scraped.")
        return

    # Normalize dates to string YYYY-MM-DD
    df_m["date"] = pd.to_datetime(df_m["date"]).dt.date.astype(str)

    # 2) Get recent prices
    tickers = sorted(df_m["ticker"].unique().tolist())
    df_p = fetch_price_table(tickers, days_back=7)
    df_p["date"] = pd.to_datetime(df_p["date"]).dt.date.astype(str)

    # 3) Merge mentions with prices
    df = df_m.merge(df_p, on=["date", "ticker"], how="left")

    # 4) Append to history if file exists
    if os.path.exists(OUT_FILE):
        try:
            old = pd.read_csv(OUT_FILE, encoding="utf-8")
        except UnicodeDecodeError:
            print("⚠️ Existing CSV not UTF-8, falling back to latin1")
            old = pd.read_csv(OUT_FILE, encoding="latin1")
        all_ = pd.concat([old, df], ignore_index=True)
        all_ = all_.drop_duplicates(subset=["date", "ticker"], keep="last")
    else:
        all_ = df

    # 5) Save in UTF-8 to avoid future decode errors
    all_.to_csv(OUT_FILE, index=False, encoding="utf-8")
    print(f"✅ Saved {len(all_)} total rows to {OUT_FILE}")

if __name__ == "__main__":
    main()
