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


def render_geographic_news_map():
    """Render the Geographic News Map interface"""
    st.title("🗺️ Geographic News Mapper")
    st.write("Explore news stories plotted on an interactive world map based on their geographic relevance.")
    
    # Input for search query
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Enter news topic to search:", 
                             placeholder="e.g., climate change, technology, politics")
    with col2:
        search_button = st.button("🔍 Search & Map", type="primary")
    
    if search_button and query:
        with st.spinner("Fetching and analyzing news articles..."):
            news_data = fetch_geographic_news(query, max_results=20)
            
            if news_data:
                # Create and display the map
                fig = create_world_map(news_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display summary statistics
                display_geographic_summary(news_data)
                
                # Display articles by region
                display_articles_by_region(news_data)
                
                # Show info about Global articles if many exist
                global_count = sum(1 for item in news_data if item['country'] == 'Global')
                if global_count > len(news_data) * 0.5:  # If more than 50% are Global
                    st.info(f"ℹ️ {global_count} out of {len(news_data)} articles were categorized as 'Global' "
                           "as they didn't contain specific geographic references. "
                           "Try searching for location-specific terms for more precise mapping.")
            else:
                st.warning("No news articles found for this topic. Please try a different search term.")
    
    elif not query and search_button:
        st.warning("Please enter a search topic first.")


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
            total_articles = len(data['articles'])
            
            st.write(f"📰 Found {total_articles} articles, processing for geographic data...")
            
            for i, article in enumerate(data['articles']):
                # Extract geographic information (now always returns a location)
                location_info = extract_location_from_article(article)
                
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
            
            st.success(f"✅ Successfully mapped {len(news_data)} articles to geographic locations!")
            return news_data
        else:
            st.warning("No articles found from News API. Please check your API key or try a different search term.")
            return []
        
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []


def extract_location_from_article(article):
    """Extract geographic information from article content"""
    text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
    
    # Enhanced location database with more variations
    location_database = {
        # United States variations
        'united states': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'usa': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'america': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'us': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        'new york': {'country': 'United States', 'city': 'New York', 'lat': 40.7128, 'lon': -74.0060},
        'california': {'country': 'United States', 'city': 'Los Angeles', 'lat': 34.0522, 'lon': -118.2437},
        'texas': {'country': 'United States', 'city': 'Austin', 'lat': 30.2672, 'lon': -97.7431},
        'florida': {'country': 'United States', 'city': 'Miami', 'lat': 25.7617, 'lon': -80.1918},
        'washington': {'country': 'United States', 'city': 'Washington D.C.', 'lat': 38.9072, 'lon': -77.0369},
        
        # United Kingdom variations
        'united kingdom': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'uk': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'britain': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'england': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        'london': {'country': 'United Kingdom', 'city': 'London', 'lat': 51.5074, 'lon': -0.1278},
        
        # China variations
        'china': {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        'chinese': {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        'beijing': {'country': 'China', 'city': 'Beijing', 'lat': 39.9042, 'lon': 116.4074},
        'shanghai': {'country': 'China', 'city': 'Shanghai', 'lat': 31.2304, 'lon': 121.4737},
        
        # India variations
        'india': {'country': 'India', 'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090},
        'indian': {'country': 'India', 'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090},
        'delhi': {'country': 'India', 'city': 'New Delhi', 'lat': 28.6139, 'lon': 77.2090},
        'mumbai': {'country': 'India', 'city': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
        'bangalore': {'country': 'India', 'city': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
        
        # Europe
        'europe': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        'european': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        'germany': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        'berlin': {'country': 'Germany', 'city': 'Berlin', 'lat': 52.5200, 'lon': 13.4050},
        'france': {'country': 'France', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
        'paris': {'country': 'France', 'city': 'Paris', 'lat': 48.8566, 'lon': 2.3522},
        'italy': {'country': 'Italy', 'city': 'Rome', 'lat': 41.9028, 'lon': 12.4964},
        'spain': {'country': 'Spain', 'city': 'Madrid', 'lat': 40.4168, 'lon': -3.7038},
        
        # Other major countries
        'japan': {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        'japanese': {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        'tokyo': {'country': 'Japan', 'city': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
        'russia': {'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
        'russian': {'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
        'moscow': {'country': 'Russia', 'city': 'Moscow', 'lat': 55.7558, 'lon': 37.6173},
        'brazil': {'country': 'Brazil', 'city': 'Brasília', 'lat': -15.8267, 'lon': -47.9218},
        'australia': {'country': 'Australia', 'city': 'Sydney', 'lat': -33.8688, 'lon': 151.2093},
        'canada': {'country': 'Canada', 'city': 'Toronto', 'lat': 43.6532, 'lon': -79.3832},
        'south korea': {'country': 'South Korea', 'city': 'Seoul', 'lat': 37.5665, 'lon': 126.9780},
        'korea': {'country': 'South Korea', 'city': 'Seoul', 'lat': 37.5665, 'lon': 126.9780},
        
        # Add fallback for common terms
        'global': {'country': 'Global', 'city': 'International', 'lat': 0, 'lon': 0},
        'international': {'country': 'Global', 'city': 'International', 'lat': 0, 'lon': 0},
        'worldwide': {'country': 'Global', 'city': 'International', 'lat': 0, 'lon': 0},
    }
    
    text_lower = text.lower()
    
    # Look for location mentions with better matching
    for location_key, location_data in location_database.items():
        # Use word boundaries to avoid partial matches
        import re
        pattern = r'\b' + re.escape(location_key) + r'\b'
        if re.search(pattern, text_lower):
            return {
                'country': location_data['country'],
                'city': location_data['city'],
                'latitude': location_data['lat'],
                'longitude': location_data['lon']
            }
    
    # Fallback: If no specific location found, assign to "Global"
    return {
        'country': 'Global',
        'city': 'International',
        'latitude': 20.0,  # Slightly offset from 0,0 for better visibility
        'longitude': 0.0
    }


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