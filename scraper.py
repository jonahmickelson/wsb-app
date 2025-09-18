# scraper.py
import os, json, re
from time import time
from collections import Counter
from datetime import datetime, timezone, timedelta

import praw
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

COMPANY_JSON_PATH = os.path.join("data", "company_tickers.json")
SUBREDDIT = os.getenv("WSB_SUBREDDIT", "wallstreetbets")
SUBMISSION_LIMIT = int(os.getenv("SUBMISSION_LIMIT", "2000"))   # high to cover 24h
TIME_WINDOW_HOURS = int(os.getenv("TIME_WINDOW_HOURS", "24"))
COUNT_COMMENTS = os.getenv("COUNT_COMMENTS", "true").lower() == "true"
REQUIRE_DOLLAR_FOR_SHORT = os.getenv("REQUIRE_DOLLAR_FOR_SHORT", "true").lower() == "true"

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "Rrgt0Tn8W4H5q8B2_7kF7Q")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "lAoIJZrbFulLcs3VhWGybzOga7E5lA")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "wsb-tracker by u/According_Camel_6603")

# Load mapping of valid tickers -> company title
with open(COMPANY_JSON_PATH, "r") as f:
    raw = json.load(f)
ticker_to_title = {str(r.get("ticker","")).upper(): r.get("title","") for r in raw.values() if r.get("ticker")}
valid_tickers = set(ticker_to_title.keys())

# ALL-CAPS tickers (2–5 letters), optional leading $
TICKER_RE = re.compile(r'(?<![A-Z0-9])\$?[A-Z]{2,5}\b')

def extract_tickers(text: str) -> list[str]:
    if not text: return []
    found = []
    for raw_match in TICKER_RE.findall(text):
        has_dollar = raw_match.startswith("$")
        sym = raw_match.lstrip("$")
        if sym not in valid_tickers:
            continue
        if REQUIRE_DOLLAR_FOR_SHORT and len(sym) <= 2 and not has_dollar:
            continue
        found.append(sym)
    return found

def collect_mentions_24h() -> pd.DataFrame:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    mention_counter = Counter()
    cutoff = time() - TIME_WINDOW_HOURS * 3600
    sub = reddit.subreddit(SUBREDDIT)

    for submission in sub.new(limit=SUBMISSION_LIMIT):
        if getattr(submission, "created_utc", 0) < cutoff:
            continue
        content = f"{submission.title or ''}\n{submission.selftext or ''}"
        mention_counter.update(extract_tickers(content))

        if COUNT_COMMENTS:
            submission.comments.replace_more(limit=0)
            for c in submission.comments.list():
                mention_counter.update(extract_tickers(getattr(c, "body", "")))

    # date label = UTC day for the window end (e.g., “today” UTC)
    day_utc = datetime.now(timezone.utc).date().isoformat()
    df = (pd.DataFrame(mention_counter.items(), columns=["ticker","mentions"])
            .assign(title=lambda d: d["ticker"].map(ticker_to_title),
                    date=day_utc)
            .sort_values("mentions", ascending=False)
            .reset_index(drop=True))
    return df[["date","ticker","mentions","title"]]
