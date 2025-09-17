# pipeline.py
import pandas as pd
from db import init_db, upsert_mentions, upsert_prices
from scraper import collect_mentions_24h
from prices import fetch_price_table

def run_daily():
    init_db()

    mentions = collect_mentions_24h()
    upsert_mentions(mentions[["date","ticker","mentions"]])

    tickers = mentions["ticker"].unique().tolist()
    prices = fetch_price_table(tickers, days_back=7)
    upsert_prices(prices)

    # quick join preview for the day label used in mentions
    day = mentions["date"].iloc[0]
    preview = mentions.merge(prices[prices["date"] == day], on=["date","ticker"], how="left")
    print(preview.sort_values("mentions", ascending=False).head(20))

if __name__ == "__main__":
    run_daily()
