import os
import json
import re
from time import time
from collections import Counter

import praw
import yfinance as yf
import pandas as pd
import matplotlib as plt

# =============== Config =================
COMPANY_JSON_PATH = r"C:\Users\jonah\Downloads\company_tickers.json"
SUBREDDIT = "wallstreetbets"
SUBMISSION_LIMIT = 300         # how many "new" posts to scan
TIME_WINDOW_HOURS = 24         # lookback window (hours)
COUNT_COMMENTS = True          # include comments (slower)

# Optional: require $ for 1–2 letter tickers to avoid noise like "A", "IT"
REQUIRE_DOLLAR_FOR_SHORT = True

# Reddit creds (env vars preferred; otherwise fill in directly)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "Rrgt0Tn8W4H5q8B2_7kF7Q")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "lAoIJZrbFulLcs3VhWGybzOga7E5lA")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "wsb-tracker by u/According_Camel_6603")

# =============== Load valid tickers from your JSON =================
with open(COMPANY_JSON_PATH, "r") as f:
    raw = json.load(f)

records = list(raw.values())
ticker_to_title = {
    str(rec.get("ticker", "")).upper(): rec.get("title", "")
    for rec in records if rec.get("ticker")
}
valid_tickers = set(ticker_to_title.keys())

# =============== Reddit client =================
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# =============== Ticker extraction =================
# Only match ALL-CAPS tokens (2–5 letters), with optional leading $
TICKER_RE = re.compile(r'(?<![A-Z0-9])\$?[A-Z]{2,5}\b')

def extract_tickers(text: str) -> list[str]:
    """Return a list of valid tickers that appear FULLY CAPITALIZED (e.g., NVDA, $AAPL)."""
    if not text:
        return []

    found = []
    for raw_match in TICKER_RE.findall(text):
        has_dollar = raw_match.startswith("$")
        sym = raw_match.lstrip("$")  # strip leading $ for validation

        # keep only if it's a valid ticker and fully uppercase (regex already enforces caps)
        if sym not in valid_tickers:
            continue

        # optional: require $ for very short symbols (<=2 letters)
        if REQUIRE_DOLLAR_FOR_SHORT and len(sym) <= 2 and not has_dollar:
            continue

        found.append(sym)
    return found

# =============== Collect mentions =================
mention_counter = Counter()
cutoff = time() - TIME_WINDOW_HOURS * 3600

sub = reddit.subreddit(SUBREDDIT)
for submission in sub.new(limit=SUBMISSION_LIMIT):
    if getattr(submission, "created_utc", 0) < cutoff:
        continue

    # title + body
    content = f"{submission.title or ''}\n{submission.selftext or ''}"
    mention_counter.update(extract_tickers(content))

    if COUNT_COMMENTS:
        submission.comments.replace_more(limit=0)
        for c in submission.comments.list():
            mention_counter.update(extract_tickers(getattr(c, "body", "")))

# =============== DataFrame =================
df = (
    pd.DataFrame(mention_counter.items(), columns=["ticker", "mentions"])
      .assign(title=lambda d: d["ticker"].map(ticker_to_title))
      .sort_values("mentions", ascending=False)
      .reset_index(drop=True)
)

print(df.head(25))
# To save:
# df.to_csv("wsb_mentions_last24h.csv", index=False)
