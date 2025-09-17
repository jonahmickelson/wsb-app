# db.py
from sqlalchemy import create_engine, text
from pathlib import Path

DB_PATH = Path("wsb_mentions.sqlite").as_posix()
engine = create_engine(f"sqlite:///{DB_PATH}", future=True, echo=False)

def init_db():
    ddl_mentions = """
    CREATE TABLE IF NOT EXISTS mentions (
        date TEXT NOT NULL,            -- YYYY-MM-DD (UTC day window)
        ticker TEXT NOT NULL,
        mentions INTEGER NOT NULL,
        PRIMARY KEY (date, ticker)
    );
    """
    ddl_prices = """
    CREATE TABLE IF NOT EXISTS prices (
        date TEXT NOT NULL,            -- trading date (exchange calendar)
        ticker TEXT NOT NULL,
        close REAL NOT NULL,
        ret1d REAL,                    -- close-to-close daily return
        PRIMARY KEY (date, ticker)
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl_mentions))
        conn.execute(text(ddl_prices))

def upsert_mentions(df):
    # df: columns = ["date","ticker","mentions"]
    with engine.begin() as conn:
        for _, r in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO mentions (date, ticker, mentions)
                    VALUES (:date, :ticker, :mentions)
                    ON CONFLICT(date, ticker) DO UPDATE SET mentions=excluded.mentions
                """),
                dict(date=r["date"], ticker=r["ticker"], mentions=int(r["mentions"]))
            )

def upsert_prices(df):
    # df: columns = ["date","ticker","close","ret1d"]
    with engine.begin() as conn:
        for _, r in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO prices (date, ticker, close, ret1d)
                    VALUES (:date, :ticker, :close, :ret1d)
                    ON CONFLICT(date, ticker) DO UPDATE SET close=excluded.close, ret1d=excluded.ret1d
                """),
                dict(date=r["date"], ticker=r["ticker"], close=float(r["close"]), ret1d=(None if pd.isna(r["ret1d"]) else float(r["ret1d"])))
            )

# optional helpers for API
import pandas as pd
def read_mentions(date_str):
    with engine.begin() as conn:
        return pd.read_sql(text("SELECT * FROM mentions WHERE date=:d ORDER BY mentions DESC"), conn, params={"d": date_str})

def read_join(date_str):
    q = """
    SELECT m.date, m.ticker, m.mentions, p.close, p.ret1d
    FROM mentions m
    LEFT JOIN prices p ON p.date = m.date AND p.ticker = m.ticker
    WHERE m.date = :d
    ORDER BY m.mentions DESC;
    """
    with engine.begin() as conn:
        return pd.read_sql(text(q), conn, params={"d": date_str})
