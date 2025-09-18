# scraper.py
import os
import json
import re
import praw
import pandas as pd
from collections import Counter
from time import time

# ✅ Build relative path for tickers JSON
BASE_DIR = os.path.dirname(__file__)
COMPANY_JSON_PATH = os.path.join(BASE_DIR, "data", "company_tickers.json")

with open(COMPANY_JSON_PATH, "r") as f:
    raw = json.load(f)

records = list(raw.values())
ticker_to_title = {
    str(rec.get("ticker", "")).upper(): rec.get("title", "")
    for rec in records if rec.get("ticker")
}
valid_tickers = set(ticker_to_title.keys())

# regex for ALL CAPS tickers
TICKER_RE = re.compile(r'(?<![A-Z0-9])\$?[A-Z]{2,5}\b')

def extract_tickers(text: str) -> list[str]:
    if not text:
        return []
    found = []
    for raw_match in TICKER_RE.findall(text):
        has_dollar = raw_match.startswith("$")
        sym = raw_match.lstrip("$")
        if sym not in valid_tickers:
            continue
        if len(sym) <= 2 and not has_dollar:
            continue
        found.append(sym)
    return found

def collect_mentions_24h(limit=300, hours=24, count_comments=True):
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )

    cutoff = time() - hours * 3600
    sub = reddit.subreddit("wallstreetbets")
    counter = Counter()

    for submission in sub.new(limit=limit):
        if getattr(submission, "created_utc", 0) < cutoff:
            continue
        content = f"{submission.title or ''}\n{submission.selftext or ''}"
        counter.update(extract_tickers(content))
        if count_comments:
            submission.comments.replace_more(limit=0)
            for c in submission.comments.list():
                counter.update(extract_tickers(getattr(c, "body", "")))

    today = pd.Timestamp.utcnow().normalize()
    df = pd.DataFrame(counter.items(), columns=["ticker", "mentions"])
    df["date"] = today
    return df[["date", "ticker", "mentions"]]
