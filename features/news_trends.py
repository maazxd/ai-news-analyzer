"""
News Trends Dashboard Feature
Real-time trending topics with bias analysis and credibility scoring
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
from functools import lru_cache
import os

# Get API key from environment or use a default (you should set this in your environment)
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Cache for trends data
_trends_cache = {}

def _get_cached_trends(cache_key):
    """Get cached trends data"""
    return _trends_cache.get(cache_key)

def _set_cached_trends(cache_key, data):
    """Set cached trends data"""
    _trends_cache[cache_key] = {
        'data': data,
        'timestamp': datetime.now()
    }

def _clear_old_cache():
    """Clear cache entries older than 15 minutes"""
    cutoff = datetime.now() - timedelta(minutes=15)
    keys_to_remove = []
    for key, value in _trends_cache.items():
        if value['timestamp'] < cutoff:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del _trends_cache[key]
from utils.source_data import get_source_political_leaning, get_source_credibility
from urllib.parse import urlparse


# Cache trending data for 15 minutes to avoid excessive API calls
@st.cache_data(ttl=900)  # Cache for 15 minutes
def fetch_trending_news():
    """Fetch trending news from multiple sources"""
    try:
        # Fetch more articles from multiple categories for comprehensive coverage
        categories = ['general', 'technology', 'business', 'health', 'science', 'sports']
        all_articles = []
        
        for category in categories:
            response = requests.get(
                'https://newsapi.org/v2/top-headlines',
                params={
                    'country': 'us',
                    'category': category,
                    'pageSize': 20,  # Increased from 10 to 20 per category
                    'apiKey': NEWS_API_KEY
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                # Add category info and filter valid articles
                for article in articles:
                    if (article.get('title') and 
                        article.get('url') and 
                        article.get('title') != '[Removed]' and
                        article.get('description')):
                        article['category'] = category
                        all_articles.append(article)
        
        # Also fetch from everything endpoint for more diverse content
        response = requests.get(
            'https://newsapi.org/v2/everything',
            params={
                'q': 'breaking OR trending OR latest',
                'language': 'en',
                'sortBy': 'popularity',
                'pageSize': 50,  # Get 50 more articles
                'apiKey': NEWS_API_KEY
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            
            for article in articles:
                if (article.get('title') and 
                    article.get('url') and 
                    article.get('title') != '[Removed]' and
                    article.get('description')):
                    article['category'] = 'general'
                    all_articles.append(article)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get('title', '').lower()
            if title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_articles.append(article)
        
        return unique_articles[:100]  # Return up to 100 unique articles
        
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []


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
        # Prefer extracting domain from article URL if available
        article_url = article.get('url') or ''
        domain = ''
        if article_url and re.match(r'^https?://', article_url):
            try:
                domain = urlparse(article_url).netloc.lower()
            except Exception:
                domain = ''

        # Fallback: use source name to guess domain (best-effort)
        if not domain:
            source_name = article.get('source', {}).get('name', '')
            if source_name:
                guessed = source_name.lower().replace(' ', '')
                # do not assume .com blindly; prefer guessed as domain only
                domain = guessed

        # Build a normalized input for source lookup
        lookup_input = domain if domain else ''

        # Get political leaning safely
        try:
            leaning = get_source_political_leaning(lookup_input)
        except Exception:
            leaning = 'unknown'

        if leaning in bias_data:
            bias_data[leaning] += 1
        else:
            bias_data['unknown'] += 1

        # Get credibility safely
        try:
            credibility, _ = get_source_credibility(lookup_input)
        except Exception:
            credibility = 'Unknown'

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
        _clear_old_cache()
        
        cached_data = _get_cached_trends(cache_key)
        if cached_data:
            articles = cached_data['data']
        else:
            articles = fetch_trending_news()
            if articles:
                _set_cached_trends(cache_key, articles)
        
        if articles:
            # Display total count
            st.success(f"📊 Found {len(articles)} trending articles")
            
            # Add category filter
            categories = list(set([article.get('category', 'general') for article in articles]))
            if len(categories) > 1:
                selected_category = st.selectbox(
                    "Filter by Category:",
                    options=['All'] + categories,
                    index=0
                )
                
                # Filter articles by category if selected
                if selected_category != 'All':
                    filtered_articles = [a for a in articles if a.get('category') == selected_category]
                else:
                    filtered_articles = articles
            else:
                filtered_articles = articles
            
            # Extract trending keywords from filtered articles
            trending_keywords = _extract_trending_keywords(filtered_articles)
            
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
            
            # Pagination for articles
            articles_per_page = 25
            total_pages = (len(filtered_articles) + articles_per_page - 1) // articles_per_page
            
            if total_pages > 1:
                page = st.selectbox(
                    f"Page (showing {len(filtered_articles)} articles):",
                    options=list(range(1, total_pages + 1)),
                    index=0
                )
                start_idx = (page - 1) * articles_per_page
                end_idx = start_idx + articles_per_page
                page_articles = filtered_articles[start_idx:end_idx]
            else:
                page_articles = filtered_articles
            
            # Recent headlines in grid format
            st.markdown(f"#### � Headlines (Page {page if total_pages > 1 else 1})")
            
            # Display articles in a compact grid
            for i in range(0, len(page_articles), 3):
                cols = st.columns(3)
                
                for j, col in enumerate(cols):
                    if i + j < len(page_articles):
                        article = page_articles[i + j]
                        with col:
                            # Create compact article card
                            st.markdown(f"""
                            <div style='border: 1px solid #e0e0e0; padding: 12px; margin: 8px 0; border-radius: 6px; background: #fafafa; height: 200px; overflow: hidden;'>
                                <h5 style='margin: 0 0 8px 0; color: #333; font-size: 0.9em; line-height: 1.2;'>{article.get('title', 'No Title')[:80]}{'...' if len(article.get('title', '')) > 80 else ''}</h5>
                                <p style='margin: 0 0 8px 0; color: #666; font-size: 0.8em; line-height: 1.1;'>{article.get('description', 'No description')[:100]}{'...' if len(article.get('description', '')) > 100 else ''}</p>
                                <div style='position: absolute; bottom: 12px; left: 12px; right: 12px;'>
                                    <div style='font-size: 0.7em; color: #888; margin-bottom: 6px;'>
                                        <strong>{article.get('source', {}).get('name', 'Unknown')}</strong>
                                        {' • ' + article.get('category', 'general').title() if article.get('category') else ''}
                                    </div>
                                    <a href="{article.get('url', '#')}" target="_blank" style='
                                        background: #007bff; color: white; padding: 4px 8px; 
                                        text-decoration: none; border-radius: 3px; font-size: 0.75em;
                                        display: inline-block;
                                    '>Read More</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        
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
                                # Safe link to the article if available
                                article_url = article.get('url') or ''
                                if article_url and re.match(r'^https?://', article_url):
                                    st.markdown(f"[Read full article]({article_url})")
                                else:
                                    st.write("🔗 Full article link unavailable")
                    else:
                        st.info(f"No articles found specifically about '{selected_topic}'")


# Clear cache function for development
def clear_trends_cache():
    """Clear the trends cache"""
    global _trends_cache
    _trends_cache.clear()