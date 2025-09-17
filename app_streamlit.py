# app_streamlit.py
import streamlit as st
import pandas as pd
from datetime import date as date_cls
from db import init_db, read_join, engine
from sqlalchemy import text
import altair as alt

st.set_page_config(page_title="WSB Mentions vs Performance", layout="wide")
st.title("WSB Mentions vs Stock Performance")

init_db()
default_date = date_cls.today().isoformat()
picked = st.date_input("Pick date (UTC window)", value=date_cls.fromisoformat(default_date))
date_str = picked.isoformat()

df = read_join(date_str)

if df.empty:
    st.info("No data for this date yet. Try after automation has run at 4:01 PM EST.")
else:
    st.subheader(f"Top mentions on {date_str}")

    # user types number of tickers
    topn = st.number_input("How many top tickers?", min_value=5, max_value=50, value=20, step=1)
    show = df.sort_values("mentions", ascending=False).head(topn)

    # --- Chart 1: Bar chart of mentions vs return ---
    chart = alt.Chart(show).mark_bar().encode(
        x=alt.X("ticker:N", sort="-y"),
        y=alt.Y("ret1d:Q", title="Return (%)"),
        color=alt.condition("datum.ret1d >= 0", alt.value("green"), alt.value("red")),
        tooltip=["ticker","mentions","ret1d","close"]
    ).properties(width=700, height=400, title=f"Top {topn} tickers: Mentions vs Daily Return")
    st.altair_chart(chart, use_container_width=True)

    # --- Table with colored returns ---
    def color_returns(val):
        if pd.isna(val): return ""
        color = "green" if val > 0 else "red" if val < 0 else "black"
        return f"color: {color}"

    st.dataframe(
        show.style.format({"ret1d": "{:.2f}%"}).applymap(color_returns, subset=["ret1d"]),
        use_container_width=True
    )

    # --- Chart 2: Historical chart for one ticker ---
    choice = st.selectbox("Select a ticker to view history:", df["ticker"].unique())

    if choice:
        q = text("""
        SELECT m.date, m.mentions, p.close
        FROM mentions m
        LEFT JOIN prices p ON m.date=p.date AND m.ticker=p.ticker
        WHERE m.ticker=:t
        ORDER BY m.date ASC
        """)
        hist = pd.read_sql(q, engine, params={"t": choice})

        if not hist.empty:
            base = alt.Chart(hist).encode(x="date:T")

            line = base.mark_line(color="blue").encode(
                y=alt.Y("close:Q", title="Close Price")
            )

            bars = base.mark_bar(color="orange", opacity=0.4).encode(
                y=alt.Y("mentions:Q", title="WSB Mentions")
            )

            st.subheader(f"{choice} – Price and Mentions Over Time")
            st.altair_chart(
                (line + bars).resolve_scale(y="independent").properties(height=400),
                use_container_width=True
            )
