"""
Geographic News Mapper Feature
Show news stories on an interactive world map
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import get_secret_or_env
from utils.models import analyze_sentiment
from utils.source_data import get_source_credibility
import re


def run_geographic_news_map_feature():
    st.header("🗺️ Geographic News Mapper")
    st.markdown("*Explore news stories around the world on an interactive map*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input(
            "Search for news topic:",
            placeholder="e.g., 'technology', 'economy', 'climate'",
            value="technology"
        )
    
    with col2:
        max_articles = st.selectbox(
            "Max articles:",
            [10, 20, 30, 50],
            index=1
        )
    
    if st.button("🌍 Map Global News", type="primary"):
        with st.spinner("Mapping news stories around the world..."):
            news_data = fetch_geographic_news(search_query, max_articles)
            
            if news_data:
                # Create tabs for different views
                tab1, tab2, tab3 = st.tabs(["🗺️ World Map", "📊 Regional Analysis", "📰 Story Details"])
                
                with tab1:
                    display_world_map(news_data)
                
                with tab2:
                    display_regional_analysis(news_data)
                
                with tab3:
                    display_story_details(news_data)
            else:
                st.warning("No geolocated news found for this topic. Try a different search term.")


def fetch_geographic_news(query, max_results=20):
    """Fetch news and extract geographic information"""
    api_key = get_secret_or_env("NEWS_API_KEY")
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'sortBy': 'publishedAt',
            'pageSize': max_results,
            'language': 'en',
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('articles'):
            news_data = []
            
            for article in data['articles']:
                # Extract geographic information
                location_info = extract_location_from_article(article)
                
                if location_info:
                    # Analyze sentiment
                    text_for_analysis = f"{article.get('title', '')} {article.get('description', '')}"
                    sentiment = analyze_sentiment(text_for_analysis)
                    sentiment_score = sentiment.get('compound', 0) if isinstance(sentiment, dict) else 0
                    
                    # Get source credibility
                    source_name = article.get('source', {}).get('name', 'Unknown')
                    url_domain = article.get('url', '')
                    credibility = get_source_credibility(url_domain)
                    
                    news_item = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': source_name,
                        'published_at': article.get('publishedAt', ''),
                        'country': location_info['country'],
                        'city': location_info.get('city', ''),
                        'latitude': location_info['latitude'],
                        'longitude': location_info['longitude'],
                        'sentiment_score': sentiment_score,
                        'sentiment_label': get_sentiment_label(sentiment_score),
                        'credibility': credibility[0] if credibility else 'Unknown'
                    }
                    news_data.append(news_item)
            
            return news_data
        
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []
    
    return []


def extract_location_from_article(article):
    """Extract geographic information from article content"""
    # This is a simplified location extraction
    # In a production app, you'd use a proper NLP library like spaCy or a geocoding service
    
    text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
    
    # Country mappings with major cities and coordinates
    location_database = {
        # Major countries and cities
        'united states': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'usa': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'new york': {'country': 'United States', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
        'california': {'country': 'United States', 'city': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437},
        'texas': {'country': 'United States', 'city': 'Austin', 'lat': 30.2672, 'lon': -97.7431},
        
        'united kingdom': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'uk': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'london': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        
        'china': {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        'beijing': {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        'shanghai': {'country': 'China', 'city': 'Shanghai', 'lat': 31.2304, 'lon': 121.4737},
        
        'india': {'country': 'India', 'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090},
        'delhi': {'country': 'India', 'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090},
        'mumbai': {'country': 'India', 'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
        'bangalore': {'country': 'India', 'city': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
        
        'japan': {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        'tokyo': {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        
        'germany': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        'berlin': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        
        'france': {'country': 'France', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
        'paris': {'country': 'France', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
        
        'russia': {'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
        'moscow': {'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
        
        'brazil': {'country': 'Brazil', 'city': 'Brasília', 'lat': -15.8267, 'lon': -47.9218},
        'australia': {'country': 'Australia', 'city': 'Canberra', 'lat': -35.2809, 'lon': 149.1300},
        'canada': {'country': 'Canada', 'city': 'Ottawa', 'lat': 45.4215, 'lon': -75.6972},
        
        # Add more locations as needed
    }
    
    text_lower = text.lower()
    
    # Look for location mentions
    for location_key, location_data in location_database.items():
        if location_key in text_lower:
            return {
                'country': location_data['country'],
                'city': location_data['city'],
                'latitude': location_data['lat'],
                'longitude': location_data['lon']
            }
    
    return None


def get_sentiment_label(score):
    """Convert sentiment score to label"""
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"


def display_world_map(news_data):
    """Display interactive world map with news stories"""
    st.subheader("🌍 Global News Distribution")
    
    if not news_data:
        st.warning("No geographic data available")
        return
    
    df = pd.DataFrame(news_data)
    
    # Create color mapping for sentiment
    color_map = {
        'Positive': '#2E8B57',  # Green
        'Neutral': '#4682B4',   # Blue
        'Negative': '#DC143C'   # Red
    }
    
    df['color'] = df['sentiment_label'].map(color_map)
    df['size'] = 15  # Uniform size for markers
    
    # Create the map
    fig = go.Figure()
    
    for sentiment in ['Positive', 'Neutral', 'Negative']:
        sentiment_data = df[df['sentiment_label'] == sentiment]
        
        if not sentiment_data.empty:
            fig.add_trace(go.Scattergeo(
                lon=sentiment_data['longitude'],
                lat=sentiment_data['latitude'],
                text=sentiment_data.apply(lambda row: 
                    f"<b>{row['title'][:50]}...</b><br>" +
                    f"📍 {row['city']}, {row['country']}<br>" +
                    f"📰 {row['source']}<br>" +
                    f"😊 {row['sentiment_label']}<br>" +
                    f"🏛️ {row['credibility']}", axis=1
                ),
                mode='markers',
                marker=dict(
                    size=12,
                    color=color_map[sentiment],
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                name=f"{sentiment} ({len(sentiment_data)})",
                hovertemplate="%{text}<extra></extra>"
            ))
    
    fig.update_layout(
        title="Global News Stories by Sentiment",
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth'
        ),
        height=600,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_regional_analysis(news_data):
    """Display regional analysis charts"""
    st.subheader("📊 Regional News Analysis")
    
    if not news_data:
        st.warning("No data available for analysis")
        return
    
    df = pd.DataFrame(news_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Country distribution
        country_counts = df['country'].value_counts().head(10)
        fig_countries = px.bar(
            x=country_counts.values,
            y=country_counts.index,
            orientation='h',
            title="Top Countries by News Volume",
            labels={'x': 'Number of Articles', 'y': 'Country'}
        )
        fig_countries.update_layout(height=400)
        st.plotly_chart(fig_countries, use_container_width=True)
    
    with col2:
        # Sentiment distribution
        sentiment_counts = df['sentiment_label'].value_counts()
        fig_sentiment = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="Global Sentiment Distribution",
            color_discrete_map={
                'Positive': '#2E8B57',
                'Neutral': '#4682B4',
                'Negative': '#DC143C'
            }
        )
        fig_sentiment.update_layout(height=400)
        st.plotly_chart(fig_sentiment, use_container_width=True)


def display_story_details(news_data):
    """Display detailed story information"""
    st.subheader("📰 Detailed Story Information")
    
    if not news_data:
        st.warning("No stories available")
        return
    
    # Sort by sentiment score (most positive first)
    sorted_data = sorted(news_data, key=lambda x: x['sentiment_score'], reverse=True)
    
    for i, story in enumerate(sorted_data[:10]):  # Show top 10
        with st.expander(f"📍 {story['city']}, {story['country']} - {story['title'][:50]}..."):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{story['title']}**")
                st.markdown(f"*{story['description']}*")
                st.markdown(f"🔗 [Read Full Article]({story['url']})")
            
            with col2:
                # Sentiment indicator
                sentiment_emoji = {
                    'Positive': '😊',
                    'Neutral': '😐',
                    'Negative': '😞'
                }
                st.metric(
                    "Sentiment", 
                    f"{sentiment_emoji[story['sentiment_label']]} {story['sentiment_label']}", 
                    f"{story['sentiment_score']:.2f}"
                )
                
                st.markdown(f"**Source:** {story['source']}")
                st.markdown(f"**Credibility:** {story['credibility']}")


if __name__ == "__main__":
    run_geographic_news_map_feature()