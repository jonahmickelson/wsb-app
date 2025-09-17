# api.py
from fastapi import FastAPI, Query
from db import init_db, read_mentions, read_join
from datetime import datetime, timezone
import pandas as pd

app = FastAPI(title="WSB Mentions API")

@app.on_event("startup")
def boot():
    init_db()

@app.get("/api/mentions")
def mentions(date: str = Query(None, description="YYYY-MM-DD (UTC day label)")):
    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()
    df = read_mentions(date)
    return df.to_dict(orient="records")

@app.get("/api/merge")
def merge(date: str = Query(None, description="YYYY-MM-DD (UTC day label)")):
    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()
    df = read_join(date)
    return df.to_dict(orient="records")
