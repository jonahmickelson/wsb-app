# app_streamlit.py
import os
import pandas as pd
import streamlit as st
import altair as alt
from datetime import date as date_cls

DATA_FILE = "data/mentions_history.csv"

st.set_page_config(page_title="WSB Mentions vs Performance", layout="wide")
st.title("WSB Mentions vs Stock Performance")

if not os.path.exists(DATA_FILE):
    st.info("No data yet. The daily automation will create data/mentions_history.csv after its first run.")
    st.stop()

df = pd.read_csv(DATA_FILE, parse_dates=["date"])
if df.empty:
    st.info("Data file exists but is empty. Check back after the next daily run.")
    st.stop()

# Date picker defaults to most recent date in the CSV
latest_date = df["date"].max().date()
picked = st.date_input("Pick date (UTC window)", value=latest_date)
date_str = picked.isoformat()

day = df[df["date"] == pd.to_datetime(date_str)]
if day.empty:
    st.info(f"No rows for {date_str}. Choose another date.")
    st.stop()

# --- Top-N input (typed number)
topn = st.number_input("How many top tickers?", min_value=5, max_value=50, value=20, step=1)
show = day.sort_values("mentions", ascending=False).head(topn)

st.subheader(f"Top {topn} tickers on {date_str}: % return (bars colored by sign)")

# Chart 1: bars of returns (%), green/red by sign
bar = alt.Chart(show).mark_bar().encode(
    x=alt.X("ticker:N", sort="-y"),
    y=alt.Y("ret1d:Q", title="Return (%)"),
    color=alt.condition("datum.ret1d >= 0", alt.value("green"), alt.value("red")),
    tooltip=["ticker","mentions","ret1d","close"]
).properties(height=380)
st.altair_chart(bar, use_container_width=True)

# Table with colored returns
def color_returns(val):
    if pd.isna(val): return ""
    return f"color: {'green' if val > 0 else 'red' if val < 0 else 'black'}"

st.dataframe(
    show[["ticker","mentions","ret1d","close"]]
        .style.format({"ret1d": "{:.2f}%"}).applymap(color_returns, subset=["ret1d"]),
    use_container_width=True
)

# Historical price + mentions for a selected ticker
choice = st.selectbox("Select a ticker to view history:", sorted(df["ticker"].unique()))
hist = df[df["ticker"] == choice].sort_values("date")

if not hist.empty:
    st.subheader(f"{choice} – Price (line) & WSB Mentions (bars) over time")
    base = alt.Chart(hist).encode(x=alt.X("date:T", title="Date"))

    price_line = base.mark_line().encode(
        y=alt.Y("close:Q", title="Close Price")
    )
    mention_bars = base.mark_bar(opacity=0.4).encode(
        y=alt.Y("mentions:Q", title="WSB Mentions")
    )

    st.altair_chart(
        (price_line + mention_bars).resolve_scale(y="independent").properties(height=420),
        use_container_width=True
    )
