import os
import pandas as pd
import streamlit as st
import altair as alt

BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "data", "mentions_history.csv")

st.set_page_config(page_title="WSB Mentions vs Performance", layout="wide")
st.title("WSB Mentions vs Stock Performance")

# --- Load Data ---
if not os.path.exists(DATA_FILE):
    st.info("No data yet. The GitHub Action will create data/mentions_history.csv after its first run.")
    st.stop()

df = pd.read_csv(DATA_FILE, parse_dates=["date"])
if df.empty:
    st.info("Data file exists but is empty. Check back after the next daily run.")
    st.stop()

# --- Daily Top Tickers ---
latest_date = df["date"].max().date()
picked = st.date_input("Pick date (UTC window)", value=latest_date)
date_str = picked.isoformat()

day = df[df["date"] == pd.to_datetime(date_str)]
if day.empty:
    st.info(f"No rows for {date_str}. Choose another date.")
    st.stop()

topn = st.number_input("How many top tickers?", min_value=5, max_value=50, value=20, step=1)
show = day.sort_values("mentions", ascending=False).head(topn)

st.subheader(f"Top {topn} tickers on {date_str}")

bar = alt.Chart(show).mark_bar().encode(
    x=alt.X("ticker:N", sort="-y"),
    y=alt.Y("ret1d:Q", title="Return (%)"),
    color=alt.condition("datum.ret1d >= 0", alt.value("green"), alt.value("red")),
    tooltip=["ticker", "mentions", "ret1d", "close"]
).properties(height=380)
st.altair_chart(bar, use_container_width=True)

# --- Table with Colored Returns ---
def color_returns(val):
    if pd.isna(val):
        return ""
    return f"color: {'green' if val > 0 else 'red' if val < 0 else 'black'}"

st.dataframe(
    show[["ticker", "mentions", "ret1d", "close"]]
        .style.format({"ret1d": "{:.2f}%"}).applymap(color_returns, subset=["ret1d"]),
    use_container_width=True
)

# --- Historical Chart for Selected Ticker ---
choice = st.selectbox("Select a ticker to view history:", sorted(df["ticker"].unique()))
hist = df[df["ticker"] == choice].sort_values("date")

# Add time range selection
range_option = st.radio(
    "Select time range:",
    ["1W", "1M", "6M", "1Y", "All"],
    horizontal=True
)

if not hist.empty:
    # Ensure dates are tz-naive
    hist["date"] = pd.to_datetime(hist["date"]).dt.tz_localize(None)

    # Apply time filter
    if range_option != "All":
        days_map = {"1W": 7, "1M": 30, "6M": 180, "1Y": 365}
        cutoff = (pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=days_map[range_option])).tz_localize(None)
        hist = hist[hist["date"] >= cutoff]

    st.subheader(f"{choice} – Price (line) & WSB Mentions (bars) over time")

    # Calculate dynamic y-axis limits
    min_price = hist["close"].min()
    max_price = hist["close"].max()
    y_min = min_price * 0.99   # 1% below min
    y_max = max_price * 1.01   # 1% above max

    # Price line chart with dynamic y scale
    price_chart = alt.Chart(hist).mark_line(color="blue").encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("close:Q", title="Close Price", scale=alt.Scale(domain=[y_min, y_max])),
        tooltip=["date:T", "close:Q"]
    ).properties(height=300)

    # Mentions as bars (separate chart below)
    mentions_chart = alt.Chart(hist).mark_bar(opacity=0.5, color="orange").encode(
        x=alt.X("date:T"),
        y=alt.Y("mentions:Q", title="WSB Mentions"),
        tooltip=["date:T", "mentions:Q"]
    ).properties(height=100)

    # Stack vertically (price on top, mentions below)
    chart = alt.vconcat(price_chart, mentions_chart).resolve_scale(x="shared")

    st.altair_chart(chart, use_container_width=True)
