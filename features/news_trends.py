"""
News Trends & Search Feature
Search trending topics and current news with filtering options
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse

# Get API key from environment
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'your_news_api_key_here')

def run_news_trends_feature():
    """Main function for News Trends & Search feature"""
    
    st.markdown("## 🔥 News Trends & Search")
    st.markdown("Search for trending topics and current news with advanced filtering")
    
    # Create search interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search input
        search_query = st.text_input(
            "🔍 Search News Topics",
            placeholder="e.g., NYC election, politics, Telangana bus collapse, Jubilee Hills bypoll...",
            help="Enter keywords, events, or topics you want to search for"
        )
    
    with col2:
        # Quick filters
        st.markdown("**Quick Filters:**")
        filter_category = st.selectbox(
            "Category",
            ["All", "Politics", "Business", "Technology", "Health", "Sports", "Entertainment"],
            help="Filter by news category"
        )
    
    # Additional filters
    col3, col4, col5 = st.columns(3)
    
    with col3:
        time_range = st.selectbox(
            "Time Range",
            ["Today", "This Week", "This Month"],
            help="Filter by publication date"
        )
    
    with col4:
        country = st.selectbox(
            "Region",
            ["Global", "India", "US", "UK", "Australia"],
            help="Filter by region/country"
        )
    
    with col5:
        sort_by = st.selectbox(
            "Sort By",
            ["Relevance", "Latest", "Popular"],
            help="Sort results by criteria"
        )
    
    # Trending topics section
    st.markdown("---")
    st.markdown("### 🔥 Currently Trending")
    
    # Popular search terms (you can customize these based on current events)
    trending_topics = [
        "NYC election 2024", "US politics", "India elections", "AI technology",
        "Climate change", "Stock market", "Cryptocurrency", "Sports news",
        "Telangana news", "Mumbai news", "Delhi news", "International news",
        "Mamdani controversy", "Jubilee Hills bypoll", "Bus collapse news",
        "Election results", "Political updates", "Breaking news"
    ]
    
    # Display trending topics as clickable buttons
    cols = st.columns(4)
    for i, topic in enumerate(trending_topics):
        with cols[i % 4]:
            if st.button(f"#{topic}", key=f"trend_{i}"):
                search_query = topic
                st.rerun()
    
    # Search button
    st.markdown("---")
    if st.button("🔍 Search News", type="primary", use_container_width=True):
        if search_query:
            search_news(search_query, filter_category, time_range, country, sort_by)
        else:
            st.warning("Please enter a search term or click on a trending topic")
    
    # Show recent searches if any
    if 'recent_searches' not in st.session_state:
        st.session_state.recent_searches = []
    
    if st.session_state.recent_searches:
        st.markdown("### 📋 Recent Searches")
        recent_cols = st.columns(min(len(st.session_state.recent_searches[:5]), 5))
        for i, recent in enumerate(st.session_state.recent_searches[:5]):
            with recent_cols[i]:
                if st.button(recent, key=f"recent_{i}"):
                    search_query = recent
                    st.rerun()


def search_news(query, category, time_range, country, sort_by):
    """Search for news based on query and filters"""
    
    # Add to recent searches
    if 'recent_searches' not in st.session_state:
        st.session_state.recent_searches = []
    
    if query not in st.session_state.recent_searches:
        st.session_state.recent_searches.insert(0, query)
        st.session_state.recent_searches = st.session_state.recent_searches[:10]  # Keep only last 10
    
    with st.spinner(f"Searching for: {query}..."):
        articles = fetch_news_articles(query, category, time_range, country, sort_by)
    
    if articles:
        st.markdown(f"### 📰 Search Results for '{query}'")
        st.markdown(f"Found {len(articles)} articles")
        
        # Add filters for results
        col1, col2 = st.columns(2)
        with col1:
            show_count = st.selectbox("Show articles", [10, 25, 50, 100], index=1)
        with col2:
            if st.button("🔄 Refresh Results"):
                st.rerun()
        
        # Display articles in a clean format
        for i, article in enumerate(articles[:show_count]):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Article title as clickable link
                    if article.get('url'):
                        st.markdown(f"**[{article['title']}]({article['url']})**")
                    else:
                        st.markdown(f"**{article['title']}**")
                    
                    # Article description
                    if article.get('description'):
                        st.markdown(f"{article['description'][:300]}...")
                    
                    # Source and date
                    source_name = article.get('source', {}).get('name', 'Unknown')
                    published_at = article.get('publishedAt', '')
                    if published_at:
                        try:
                            date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime('%B %d, %Y at %I:%M %p')
                        except:
                            formatted_date = published_at
                    else:
                        formatted_date = 'Unknown date'
                    
                    st.caption(f"📰 {source_name} | 📅 {formatted_date}")
                
                with col2:
                    # Article image (if available)
                    if article.get('urlToImage'):
                        try:
                            st.image(article['urlToImage'], width=150)
                        except:
                            st.markdown("🖼️ *Image unavailable*")
                    
                    # Quick actions
                    if st.button("🔗 Open", key=f"read_{i}"):
                        if article.get('url'):
                            st.markdown(f"**Link:** [Open in new tab]({article['url']})")
                        else:
                            st.error("Article URL not available")
                
                st.markdown("---")
                
        # Show pagination info if more articles available
        if len(articles) > show_count:
            st.info(f"Showing {show_count} of {len(articles)} articles. Use the dropdown above to show more.")
    else:
        st.warning(f"No articles found for '{query}'. Try different keywords or filters.")


def fetch_news_articles(query, category, time_range, country, sort_by, max_articles=100):
    """Fetch news articles from News API"""
    
    if not NEWS_API_KEY or NEWS_API_KEY == 'your_news_api_key_here':
        # Return sample data when no API key is available
        return get_sample_news_data(query)
    
    try:
        # Build API parameters
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'pageSize': min(max_articles, 100),  # API limit is 100
            'sortBy': 'relevancy' if sort_by == 'Relevance' else 'publishedAt'
        }
        
        # Add category filter
        if category != "All":
            params['category'] = category.lower()
        
        # Add country filter
        country_codes = {
            'India': 'in',
            'US': 'us', 
            'UK': 'gb',
            'Australia': 'au'
        }
        if country in country_codes:
            params['country'] = country_codes[country]
        
        # Add time filter
        if time_range == "Today":
            params['from'] = datetime.now().strftime('%Y-%m-%d')
        elif time_range == "This Week":
            params['from'] = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        elif time_range == "This Month":
            params['from'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Choose endpoint based on filters
        if country != "Global" and category != "All":
            url = "https://newsapi.org/v2/top-headlines"
        else:
            url = "https://newsapi.org/v2/everything"
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == 'ok':
            return data.get('articles', [])
        else:
            st.error(f"API Error: {data.get('message', 'Unknown error')}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")
        return get_sample_news_data(query)
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return get_sample_news_data(query)


def get_sample_news_data(query):
    """Return sample news data when API is not available"""
    sample_articles = []
    
    # Create relevant sample articles based on query
    if any(keyword in query.lower() for keyword in ['election', 'politics', 'political']):
        topics = ['Election Updates', 'Political Analysis', 'Voting Results', 'Campaign News']
    elif any(keyword in query.lower() for keyword in ['technology', 'ai', 'tech']):
        topics = ['Tech Innovation', 'AI Development', 'Software Updates', 'Tech Industry']
    elif any(keyword in query.lower() for keyword in ['business', 'economy', 'market']):
        topics = ['Market Analysis', 'Business News', 'Economic Updates', 'Corporate News']
    else:
        topics = ['Breaking News', 'Latest Updates', 'Current Events', 'News Analysis']
    
    for i, topic in enumerate(topics):
        for j in range(12):  # 12 articles per topic = 48 total
            article = {
                'title': f"{topic}: {query} - Latest developments and expert analysis",
                'description': f"Comprehensive coverage of {query} with detailed analysis from multiple perspectives. This article covers the latest updates, expert opinions, and potential implications for the future.",
                'url': f"https://example-news.com/{query.replace(' ', '-')}-{topic.replace(' ', '-').lower()}-{j+1}",
                'urlToImage': None,
                'publishedAt': (datetime.now() - timedelta(hours=i*6 + j)).isoformat(),
                'source': {'name': f"{topic.split()[0]} News Network"}
            }
            sample_articles.append(article)
    
    return sample_articles


# Clear cache function for development
def clear_trends_cache():
    """Clear the trends cache"""
    st.cache_data.clear()