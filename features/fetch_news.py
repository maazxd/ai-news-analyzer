"""
Fetch Live News Feature
Gets latest news articles from around the world using NewsAPI
"""
import streamlit as st
import requests


def run_fetch_news_feature():
    """Main function for Fetch Live News feature"""
    
    # Feature header
    st.markdown("""
    <div class='feature-description'>
        <h2 style='margin:0 0 0.5rem 0; color:white;'>🌐 Fetch Live News</h2>
        <p style='margin:0; font-size:1.05em; opacity:0.95;'>
            Get the latest news articles from around the world, filtered by your interests
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    API_KEY = "589661b2aac34f7991bf7c4160fa7b57"
    
    # Search parameters
    st.markdown("#### 🔍 Search Parameters")
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input(
            "Topic or Keywords",
            "technology",
            placeholder="e.g. politics, AI, climate change, sports...",
            help="Enter keywords or topics you want to search for"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort Results By",
            options=["publishedAt", "relevancy", "popularity"],
            index=0,
            format_func=lambda x: {"publishedAt": "📅 Most Recent", "relevancy": "🎯 Relevance", "popularity": "🔥 Popularity"}[x],
            help="Choose how to sort the news results"
        )

    col3, col4 = st.columns([1, 1])
    with col3:
        num_articles = st.slider(
            "Number of Articles",
            min_value=5,
            max_value=20,
            value=10,
            help="Select how many articles to fetch"
        )
    with col4:
        language = st.selectbox(
            "Language",
            options=[("en", "🇬🇧 English"), ("fr", "🇫🇷 French"), ("de", "🇩🇪 German"), ("es", "🇪🇸 Spanish")],
            index=0,
            format_func=lambda x: x[1],
            help="Select the language for news articles"
        )[0]

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("📰 Fetch Latest News", use_container_width=True, type="primary"):
        if not API_KEY or API_KEY.strip() == "":
            st.error("⚠️ Please add your NewsAPI key before using this feature.")
        elif not query.strip():
            st.warning("⚠️ Please enter a topic to search for news.")
        else:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": language,
                "pageSize": num_articles,
                "sortBy": sort_by,
                "apiKey": API_KEY
            }
            try:
                with st.spinner("🔄 Fetching latest news articles..."):
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                if data.get("status") == "ok":
                    articles = data.get("articles", [])
                    if not articles:
                        st.warning("No articles found for this topic.")
                    else:
                        st.success(f"Showing {len(articles)} articles for **{query}** ({language.upper()}) sorted by **{sort_by}**.")
                        for i, article in enumerate(articles, 1):
                            with st.expander(f"{i}. {article.get('title', 'No Title')}"):
                                st.markdown(f"**Source:** {article['source'].get('name', '')}")
                                st.markdown(f"**Author:** {article.get('author', 'Unknown')}")
                                st.markdown(f"**Published:** {article.get('publishedAt', '')[:10]}")
                                if article.get("urlToImage"):
                                    st.image(article["urlToImage"], width=400)
                                st.write(article.get("description", ""))
                                st.markdown(f"[Read full article]({article.get('url', '#')})")
                else:
                    st.error("Failed to fetch news. Check your API key or query.")
            except Exception as e:
                st.error(f"Error fetching news: {e}")
