"""
News Timeline Feature
Visualizes news coverage over time
"""
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import altair as alt


@st.cache_data(show_spinner=False)
def fetch_news_window(query, api_key, days=14, language="en") -> pd.DataFrame:
    """
    Returns a DataFrame with columns: date (datetime), source (str), title (str), url (str)
    for up to 100 recent articles in the lookback window.
    """
    url = "https://newsapi.org/v2/everything"
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "language": language,
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": 100,
        "page": 1,
        "apiKey": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.DataFrame(columns=["date", "source", "title", "url"])

    rows = []
    if data.get("status") == "ok":
        for a in data.get("articles", []):
            d = (a.get("publishedAt") or "")[:10]
            if not d:
                continue
            rows.append({
                "date": pd.to_datetime(d),
                "source": (a.get("source") or {}).get("name", "") or "Unknown",
                "title": a.get("title", "").strip() or "Untitled",
                "url": a.get("url", "#"),
            })
    return pd.DataFrame(rows)


def run_timeline_feature():
    """Main function for News Timeline feature"""
    
    st.subheader("📊 News Timeline Visualization")

    topic = st.text_input("Enter a topic to visualize news trend:", "AI")
    col_tl1, col_tl2, col_tl3 = st.columns([1, 1, 1])
    with col_tl1:
        days = st.slider("Days to look back", min_value=7, max_value=60, value=14)
    with col_tl2:
        language = st.selectbox(
            "Language",
            options=[("en", "English"), ("fr", "French"), ("de", "German"), ("es", "Spanish")],
            index=0,
            format_func=lambda x: x[1]
        )[0]
    with col_tl3:
        smooth = st.slider("Smoothing (days)", min_value=1, max_value=7, value=3, help="Moving average window")

    API_KEY = "589661b2aac34f7991bf7c4160fa7b57"

    @st.cache_data(show_spinner=False)
    def get_window_df_cached(q, key, d, lang):
        return fetch_news_window(q, key, days=d, language=lang)

    if st.button("Show Timeline", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Fetching coverage..."):
                df = get_window_df_cached(topic, API_KEY, days, language)

            if df.empty:
                st.info("No news articles found for this topic and time range.")
            else:
                # Build daily series
                daily = df.groupby("date").size().rename("count")
                idx = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
                daily = daily.reindex(idx, fill_value=0)

                # Main chart: area chart of daily article counts
                st.subheader("Daily Article Count")
                st.bar_chart(daily)

                # ----------------- TABS FOR SOURCES / HEADLINES -----------------
                tab1, tab2, tab3 = st.tabs(["📅 Coverage by Day", "📊 Top Sources", "📰 Exact Headlines"])

                with tab1:
                    st.markdown("#### Daily Coverage Overview")
                    st.write("Shows the number of articles published each day.")
                    st.bar_chart(daily)

                with tab2:
                    # Top sources selector
                    src_counts = df["source"].value_counts()
                    top_n = st.slider("Top sources to display", 3, min(12, len(src_counts)), min(5, len(src_counts)))
                    default_sources = list(src_counts.head(top_n).index)
                    selected_sources = st.multiselect("Sources", options=list(src_counts.index), default=default_sources)
                    if selected_sources:
                        df_src = (
                            df[df["source"].isin(selected_sources)]
                            .groupby(["date", "source"])
                            .size()
                            .reset_index(name="count")
                        )
                        chart = alt.Chart(df_src).mark_area().encode(
                            x=alt.X("date:T", title="Date"),
                            y=alt.Y("count:Q", stack="normalize", title="Share of daily coverage"),
                            color=alt.Color("source:N", legend=alt.Legend(title="Source")),
                            tooltip=["date:T", "source:N", "count:Q"]
                        ).properties(height=320)
                        st.altair_chart(chart, use_container_width=True)
                        st.caption("Stacked area shows share by source each day.")
                    else:
                        st.info("Select at least one source.")

                with tab3:
                    # Exact headlines per day (grouped with source)
                    for d, sub in df.sort_values("date").groupby(df["date"].dt.date):
                        with st.expander(f"{d} — {len(sub)} articles"):
                            for _, row in sub.iterrows():
                                st.markdown(f"- [{row['title']}]({row['url']}) • {row['source']}")
