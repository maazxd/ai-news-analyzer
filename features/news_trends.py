"""
News Trends Dashboard Feature
Real-time trending topics analysis with bias distribution
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import re
from functools import lru_cache
import plotly.express as px
import plotly.graph_objects as go
from utils.source_data import get_source_political_leaning, get_source_credibility


# Cache trending data for 15 minutes to avoid excessive API calls
@lru_cache(maxsize=32)
def _get_cached_trends(cache_key: str):
    """Cache trending topics data with timestamp"""
    return _fetch_trending_topics_raw()


def _fetch_trending_topics_raw():
    """Fetch trending topics from News API"""
    try:
        # Using News API for trending topics (you'll need an API key)
        api_key = "your_news_api_key_here"  # Replace with actual API key
        
        # Get top headlines from multiple sources
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            'apiKey': api_key,
            'country': 'us',
            'pageSize': 100,
            'language': 'en'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
        else:
            # Fallback: return sample data for development
            return _get_sample_trending_data()
            
    except Exception as e:
        st.error(f"Error fetching trends: {e}")
        return _get_sample_trending_data()


def _get_sample_trending_data():
    """Sample data for development/testing"""
    return [
        {
            'title': 'Election Results Show Major Shift in Voter Preferences',
            'source': {'name': 'CNN'},
            'publishedAt': '2025-11-05T10:00:00Z',
            'description': 'Latest election results indicate significant changes...',
            'url': 'https://cnn.com/sample'
        },
        {
            'title': 'Climate Summit Reaches Historic Agreement',
            'source': {'name': 'BBC News'},
            'publishedAt': '2025-11-05T09:30:00Z',
            'description': 'World leaders agree on ambitious climate targets...',
            'url': 'https://bbc.com/sample'
        },
        {
            'title': 'Tech Giants Face New Regulation Proposals',
            'source': {'name': 'Reuters'},
            'publishedAt': '2025-11-05T08:45:00Z',
            'description': 'Government proposes stricter oversight of major tech companies...',
            'url': 'https://reuters.com/sample'
        },
        {
            'title': 'Economic Indicators Point to Market Volatility',
            'source': {'name': 'Wall Street Journal'},
            'publishedAt': '2025-11-05T07:15:00Z',
            'description': 'Financial experts warn of potential market fluctuations...',
            'url': 'https://wsj.com/sample'
        }
    ]


def _extract_trending_keywords(articles):
    """Extract and rank trending keywords from articles"""
    # Combine all titles and descriptions
    text_corpus = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        text_corpus.append(f"{title} {description}".lower())
    
    # Join all text
    full_text = ' '.join(text_corpus)
    
    # Extract meaningful words (filter out common words)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
        'this', 'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
        'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'
    }
    
    # Extract words (3+ characters, alphanumeric)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', full_text)
    meaningful_words = [word for word in words if word not in stop_words]
    
    # Count frequency
    word_counts = Counter(meaningful_words)
    
    # Return top trending keywords
    return word_counts.most_common(20)


def _analyze_source_bias_distribution(articles):
    """Analyze how different political leanings cover trending topics"""
    bias_data = {'left-leaning': 0, 'center': 0, 'right-leaning': 0, 'unknown': 0}
    credibility_data = {'High Credibility': 0, 'Mixed Credibility': 0, 'Low Credibility': 0, 'Unknown': 0}
    
    for article in articles:
        source_name = article.get('source', {}).get('name', '')
        source_url = f"https://{source_name.lower().replace(' ', '')}.com"
        
        # Get political leaning
        leaning = get_source_political_leaning(source_url)
        if leaning in bias_data:
            bias_data[leaning] += 1
        else:
            bias_data['unknown'] += 1
            
        # Get credibility
        credibility, _ = get_source_credibility(source_url)
        if credibility in credibility_data:
            credibility_data[credibility] += 1
        else:
            credibility_data['Unknown'] += 1
    
    return bias_data, credibility_data


def run_news_trends_feature():
    """Main function for News Trends Dashboard"""
    
    # Feature header
    st.markdown("""
    <div class='feature-description'>
        <h2 style='margin:0 0 0.5rem 0; color:white;'>📈 News Trends Dashboard</h2>
        <p style='margin:0; font-size:1.05em; opacity:0.95;'>
            Real-time trending topics with bias distribution analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🔥 Trending Now", "📊 Bias Analysis", "🎯 Topic Deep Dive"])
    
    with tab1:
        st.markdown("### 🔥 Currently Trending Topics")
        
        # Add refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("Last updated: Live data")
        with col2:
            if st.button("🔄 Refresh", key="refresh_trends"):
                st.rerun()
        
        # Fetch trending data
        cache_key = f"trends_{datetime.now().strftime('%Y%m%d_%H%M')}"
        articles = _get_cached_trends(cache_key)
        
        if articles:
            # Extract trending keywords
            trending_keywords = _extract_trending_keywords(articles)
            
            # Display top trending keywords
            st.markdown("#### 🏷️ Top Trending Keywords")
            
            if trending_keywords:
                # Create keyword frequency chart
                keywords_df = pd.DataFrame(trending_keywords[:10], columns=['Keyword', 'Frequency'])
                
                fig = px.bar(
                    keywords_df, 
                    x='Frequency', 
                    y='Keyword',
                    orientation='h',
                    title="Most Mentioned Keywords",
                    color='Frequency',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Display keyword tags
                st.markdown("**Trending Keywords:**")
                keyword_tags = []
                for keyword, count in trending_keywords[:15]:
                    keyword_tags.append(f"`{keyword}` ({count})")
                st.markdown(" • ".join(keyword_tags))
            
            # Recent headlines
            st.markdown("#### 📰 Latest Headlines")
            for i, article in enumerate(articles[:8]):
                with st.expander(f"📄 {article.get('title', 'No title')[:80]}..."):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Source:** {article.get('source', {}).get('name', 'Unknown')}")
                        st.write(f"**Description:** {article.get('description', 'No description')}")
                        if article.get('url'):
                            st.markdown(f"[Read full article]({article['url']})")
                    with col2:
                        # Show source credibility
                        source_name = article.get('source', {}).get('name', '')
                        source_url = f"https://{source_name.lower().replace(' ', '')}.com"
                        credibility, _ = get_source_credibility(source_url)
                        leaning = get_source_political_leaning(source_url)
                        
                        if credibility == "High Credibility":
                            st.success("✅ High Credibility")
                        elif credibility == "Mixed Credibility":
                            st.warning("⚠️ Mixed Credibility")
                        else:
                            st.info("❓ Unknown Credibility")
                        
                        st.caption(f"Leaning: {leaning.title()}")
        
        else:
            st.warning("⚠️ Unable to fetch trending data. Please try again later.")
    
    with tab2:
        st.markdown("### 📊 Bias Distribution Analysis")
        
        if articles:
            # Analyze bias distribution
            bias_data, credibility_data = _analyze_source_bias_distribution(articles)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ⚖️ Political Leaning Distribution")
                
                # Create bias pie chart
                bias_df = pd.DataFrame(list(bias_data.items()), columns=['Leaning', 'Count'])
                bias_df = bias_df[bias_df['Count'] > 0]  # Remove zero counts
                
                if not bias_df.empty:
                    fig_bias = px.pie(
                        bias_df, 
                        values='Count', 
                        names='Leaning',
                        title="Source Political Leaning",
                        color_discrete_map={
                            'left-leaning': '#3498db',
                            'center': '#2ecc71',
                            'right-leaning': '#e74c3c',
                            'unknown': '#95a5a6'
                        }
                    )
                    st.plotly_chart(fig_bias, use_container_width=True)
                
                # Display metrics
                for leaning, count in bias_data.items():
                    if count > 0:
                        percentage = (count / len(articles)) * 100
                        st.metric(leaning.title().replace('-', ' '), f"{count} sources", f"{percentage:.1f}%")
            
            with col2:
                st.markdown("#### 🏆 Credibility Distribution")
                
                # Create credibility pie chart
                cred_df = pd.DataFrame(list(credibility_data.items()), columns=['Credibility', 'Count'])
                cred_df = cred_df[cred_df['Count'] > 0]  # Remove zero counts
                
                if not cred_df.empty:
                    fig_cred = px.pie(
                        cred_df, 
                        values='Count', 
                        names='Credibility',
                        title="Source Credibility",
                        color_discrete_map={
                            'High Credibility': '#27ae60',
                            'Mixed Credibility': '#f39c12',
                            'Low Credibility': '#e74c3c',
                            'Unknown': '#95a5a6'
                        }
                    )
                    st.plotly_chart(fig_cred, use_container_width=True)
                
                # Display metrics
                for credibility, count in credibility_data.items():
                    if count > 0:
                        percentage = (count / len(articles)) * 100
                        st.metric(credibility, f"{count} sources", f"{percentage:.1f}%")
        
        else:
            st.warning("⚠️ No data available for bias analysis.")
    
    with tab3:
        st.markdown("### 🎯 Topic Deep Dive")
        st.info("🚧 **Coming Soon:** Deep dive analysis into specific trending topics with timeline view and cross-source comparison.")
        
        # Placeholder for future implementation
        if articles:
            trending_keywords = _extract_trending_keywords(articles)
            
            if trending_keywords:
                selected_topic = st.selectbox(
                    "Select a trending topic to analyze:",
                    options=[keyword for keyword, _ in trending_keywords[:10]]
                )
                
                if selected_topic:
                    st.markdown(f"#### 📊 Analysis for: **{selected_topic.title()}**")
                    
                    # Filter articles containing the selected keyword
                    topic_articles = []
                    for article in articles:
                        title = article.get('title', '').lower()
                        description = article.get('description', '').lower()
                        if selected_topic in title or selected_topic in description:
                            topic_articles.append(article)
                    
                    if topic_articles:
                        st.success(f"Found {len(topic_articles)} articles about '{selected_topic}'")
                        
                        # Show how different sources cover this topic
                        for article in topic_articles[:5]:
                            source_name = article.get('source', {}).get('name', 'Unknown')
                            source_url = f"https://{source_name.lower().replace(' ', '')}.com"
                            leaning = get_source_political_leaning(source_url)
                            
                            with st.expander(f"{source_name} ({leaning})"):
                                st.write(f"**Title:** {article.get('title')}")
                                st.write(f"**Description:** {article.get('description')}")
                                if article.get('url'):
                                    st.markdown(f"[Read full article]({article['url']})")
                    else:
                        st.info(f"No articles found specifically about '{selected_topic}'")


# Clear cache function for development
def clear_trends_cache():
    """Clear the trends cache"""
    _get_cached_trends.cache_clear()