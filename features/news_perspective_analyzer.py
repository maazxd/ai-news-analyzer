"""
News Perspective Analyzer - Comprehensive Bias Analysis Feature

This feature analyzes how the same news story is reported across different sources
with varying political leanings and geographical locations, providing users with
a 360-degree view of news coverage.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time

# Import existing utilities
from utils.helpers import get_secret_or_env
from utils.models import analyze_sentiment
from utils.source_data import get_source_credibility


# Source categories with political bias classifications
NEWS_SOURCES = {
    'left': {
        'cnn': 'CNN',
        'guardian': 'The Guardian', 
        'msnbc': 'MSNBC',
        'huffpost': 'HuffPost',
        'washingtonpost': 'Washington Post'
    },
    'center': {
        'reuters': 'Reuters',
        'bbc': 'BBC News',
        'ap': 'Associated Press',
        'npr': 'NPR',
        'axios': 'Axios'
    },
    'right': {
        'fox': 'Fox News',
        'wsj': 'Wall Street Journal',
        'nypost': 'New York Post',
        'dailymail': 'Daily Mail',
        'breitbart': 'Breitbart'
    }
}

# Color scheme for bias visualization
BIAS_COLORS = {
    'left': '#4472C4',     # Blue
    'center': '#70AD47',   # Green  
    'right': '#E15759'     # Red
}


def render_news_perspective_analyzer():
    """Main render function for the News Perspective Analyzer"""
    st.title("🎯 News Perspective Analyzer")
    st.write("**Discover how the same story is told differently across the political spectrum**")
    
    # Feature introduction
    with st.expander("📖 How This Works", expanded=False):
        st.markdown("""
        **The News Perspective Analyzer reveals media bias by comparing how different sources report the same story:**
        
        🔍 **Multi-Source Collection**: Fetches articles about your topic from diverse political perspectives
        
        📊 **Bias Spectrum Visualization**: Interactive chart showing political alignment vs sentiment analysis
        
        🔄 **Side-by-Side Comparison**: Headlines, sentiment scores, and credibility ratings compared
        
        💡 **Key Differences Analysis**: Highlights contradictions, common themes, and missing information
        
        🎯 **Educational Value**: Helps users identify bias patterns and think more critically about news consumption
        """)
    
    # Sample topics for better user experience
    st.markdown("### 💡 Try These Popular Topics:")
    sample_topics = ["climate change", "economic policy", "healthcare", "technology regulation", "immigration"]
    
    cols = st.columns(5)
    for i, topic in enumerate(sample_topics):
        with cols[i]:
            if st.button(f"📰 {topic.title()}", key=f"sample_{i}"):
                st.session_state.analysis_topic = topic
    
    # Input section
    st.subheader("🔎 Analyze News Coverage")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "Enter a news topic to analyze across the political spectrum:",
            placeholder="e.g., climate summit, election results, economic policy",
            value=st.session_state.get('analysis_topic', ''),
            key="topic_input"
        )
    
    with col2:
        analyze_button = st.button("🔍 Analyze Coverage", type="primary")
    
    # Clear previous topic selection
    if topic != st.session_state.get('analysis_topic', ''):
        if 'analysis_topic' in st.session_state:
            del st.session_state.analysis_topic
    
    if analyze_button and topic:
        analyze_news_perspective(topic)
    elif analyze_button and not topic:
        st.warning("⚠️ Please enter a news topic to analyze")


def analyze_news_perspective(topic):
    """Main analysis function that orchestrates the entire perspective analysis"""
    if not topic or len(topic.strip()) < 3:
        st.error("⚠️ Please enter a topic with at least 3 characters")
        return
    
    with st.spinner("🔍 Analyzing news coverage across the political spectrum..."):
        # Step 1: Collect articles from different sources
        st.write("📰 **Step 1**: Collecting articles from diverse sources...")
        articles_by_bias = collect_multi_source_articles(topic)
        
        # Check if we have any articles
        total_articles = sum(len(articles) for articles in articles_by_bias.values())
        if total_articles == 0:
            st.error("❌ No articles found for this topic. Please try:")
            st.markdown("""
            - A more general topic (e.g., "climate change" instead of specific event names)
            - Current news topics (articles from the last week)
            - Topics that major news outlets typically cover
            """)
            return
        
        # Check if we have bias diversity
        bias_categories_found = sum(1 for articles in articles_by_bias.values() if len(articles) > 0)
        if bias_categories_found < 2:
            st.warning("⚠️ Limited political diversity in sources found. Results may not show comprehensive bias analysis.")
        
        # Step 2: Analyze sentiment and bias
        st.write("🧠 **Step 2**: Analyzing sentiment and bias patterns...")
        analyzed_articles = analyze_articles_sentiment_bias(articles_by_bias)
        
        if not analyzed_articles:
            st.error("❌ Failed to analyze articles. Please try again.")
            return
        
        # Step 3: Create visualizations
        st.write("📊 **Step 3**: Creating bias spectrum visualization...")
        create_bias_spectrum_chart(analyzed_articles)
        
        # Step 4: Side-by-side comparison
        st.write("🔄 **Step 4**: Generating side-by-side comparison...")
        create_side_by_side_comparison(analyzed_articles)
        
        # Step 5: Key differences analysis
        st.write("💡 **Step 5**: Analyzing key differences and insights...")
        analyze_key_differences(analyzed_articles)
        
        # Success message
        st.success(f"🎯 **Analysis Complete!** Successfully analyzed {len(analyzed_articles)} articles across {bias_categories_found} political perspectives.")


def collect_multi_source_articles(topic, max_per_bias=2):
    """Collect articles from different bias categories"""
    api_key = get_secret_or_env("NEWS_API_KEY")
    articles_by_bias = {'left': [], 'center': [], 'right': []}
    
    if not api_key:
        st.error("❌ News API key not configured. Please check your environment settings.")
        return articles_by_bias
    
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    try:
        # Use general search first, then filter by domain
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': topic,
            'sortBy': 'publishedAt',
            'pageSize': 50,  # Get more articles to filter from
            'language': 'en',
            'apiKey': api_key,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  # Last 7 days
        }
        
        progress_text.text("Fetching articles from News API...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if not data.get('articles'):
            st.warning("⚠️ No articles found for this topic from News API")
            progress_bar.empty()
            progress_text.empty()
            return articles_by_bias
        
        progress_text.text("Categorizing articles by political bias...")
        
        # Categorize articles by source bias
        all_articles = data['articles']
        categorized_count = 0
        
        for article in all_articles:
            source_name = article.get('source', {}).get('name', '').lower()
            article_url = article.get('url', '').lower()
            
            # Determine bias category based on source
            bias_category = determine_source_bias(source_name, article_url)
            
            if bias_category and len(articles_by_bias[bias_category]) < max_per_bias:
                processed_article = process_article(article, bias_category)
                if processed_article:
                    articles_by_bias[bias_category].append(processed_article)
                    categorized_count += 1
            
            # Update progress
            progress = min(categorized_count / (max_per_bias * 3), 1.0)
            progress_bar.progress(progress)
            
            # Stop if we have enough articles from each category
            if all(len(articles_by_bias[bias]) >= max_per_bias for bias in ['left', 'center', 'right']):
                break
        
        progress_bar.empty()
        progress_text.empty()
        
        # Display collection summary
        total_articles = sum(len(articles) for articles in articles_by_bias.values())
        if total_articles > 0:
            st.success(f"✅ Successfully categorized {total_articles} articles across the political spectrum")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Left-leaning", len(articles_by_bias['left']))
            with col2:
                st.metric("Center", len(articles_by_bias['center']))
            with col3:
                st.metric("Right-leaning", len(articles_by_bias['right']))
        else:
            st.warning("⚠️ Could not categorize any articles by political bias. Try a more specific topic.")
        
        return articles_by_bias
        
    except requests.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        progress_bar.empty()
        progress_text.empty()
        return articles_by_bias
    except Exception as e:
        st.error(f"❌ Error collecting articles: {str(e)}")
        progress_bar.empty()
        progress_text.empty()
        return articles_by_bias


def determine_source_bias(source_name, article_url):
    """Determine political bias category based on source name and URL"""
    # Enhanced source mapping with more sources
    source_mapping = {
        'left': [
            'cnn', 'guardian', 'msnbc', 'huffpost', 'washington post', 'washingtonpost',
            'new york times', 'nytimes', 'atlantic', 'vox', 'mother jones', 'salon',
            'daily beast', 'buzzfeed', 'slate', 'politico', 'abc news', 'cbs news'
        ],
        'center': [
            'reuters', 'bbc', 'associated press', 'ap news', 'npr', 'axios',
            'pbs', 'usa today', 'usatoday', 'time', 'newsweek', 'bloomberg',
            'financial times', 'christian science monitor', 'the hill'
        ],
        'right': [
            'fox news', 'foxnews', 'wall street journal', 'wsj', 'new york post',
            'nypost', 'daily mail', 'breitbart', 'national review', 'washington times',
            'daily wire', 'townhall', 'federalist', 'washington examiner'
        ]
    }
    
    # Check source name and URL for bias indicators
    text_to_check = f"{source_name} {article_url}".lower()
    
    for bias_type, sources in source_mapping.items():
        for source in sources:
            if source in text_to_check:
                return bias_type
    
    return None  # Unknown bias


def process_article(article, bias_type):
    """Process individual article and extract relevant information"""
    try:
        # Get source information
        source_name = article.get('source', {}).get('name', 'Unknown')
        url = article.get('url', '')
        
        # Get credibility rating
        credibility_info = get_source_credibility(url)
        credibility = credibility_info[0] if credibility_info else 'Unknown'
        
        processed = {
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'url': url,
            'source': source_name,
            'published_at': article.get('publishedAt', ''),
            'bias_category': bias_type,
            'credibility': credibility,
            'content_preview': article.get('content', '')[:500] if article.get('content') else ''
        }
        
        return processed
        
    except Exception:
        return None


def analyze_articles_sentiment_bias(articles_by_bias):
    """Analyze sentiment for all collected articles"""
    analyzed_articles = []
    
    total_articles = sum(len(articles) for articles in articles_by_bias.values())
    if total_articles == 0:
        return analyzed_articles
        
    progress_bar = st.progress(0)
    current_article = 0
    
    for bias_type, articles in articles_by_bias.items():
        for article in articles:
            try:
                # Analyze sentiment with better text preparation
                title = article.get('title', '')
                description = article.get('description', '')
                
                # Ensure we have text to analyze
                if not title and not description:
                    text_for_analysis = "No content available"
                else:
                    text_for_analysis = f"{title}. {description}".strip()
                
                # Call sentiment analysis
                sentiment_result = analyze_sentiment(text_for_analysis)
                
                # Handle different return formats from sentiment analysis
                if isinstance(sentiment_result, dict):
                    # VADER-style return with compound score
                    sentiment_score = sentiment_result.get('compound', 0)
                elif isinstance(sentiment_result, (int, float)):
                    # Direct numerical score
                    sentiment_score = float(sentiment_result)
                else:
                    # Fallback: analyze manually based on text
                    sentiment_score = simple_sentiment_analysis(text_for_analysis)
                
                # Ensure score is in valid range
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
                sentiment_label = get_sentiment_label(sentiment_score)
                
                # Add analysis results
                article['sentiment_score'] = sentiment_score
                article['sentiment_label'] = sentiment_label
                article['bias_score'] = get_bias_score(bias_type)
                
                analyzed_articles.append(article)
                
            except Exception as e:
                # Fallback for failed sentiment analysis
                st.warning(f"⚠️ Sentiment analysis failed for article: {e}")
                article['sentiment_score'] = 0.0
                article['sentiment_label'] = 'Neutral'
                article['bias_score'] = get_bias_score(bias_type)
                analyzed_articles.append(article)
            
            current_article += 1
            progress_bar.progress(current_article / total_articles)
    
    progress_bar.empty()
    return analyzed_articles


def simple_sentiment_analysis(text):
    """Simple fallback sentiment analysis using keyword matching"""
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    # Positive keywords
    positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win', 'victory', 'progress', 'improve', 'better', 'strong', 'up', 'rise', 'gain', 'benefit', 'growth']
    
    # Negative keywords  
    negative_words = ['bad', 'terrible', 'negative', 'fail', 'failure', 'lose', 'loss', 'decline', 'worse', 'weak', 'down', 'fall', 'crisis', 'problem', 'concern', 'worry']
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    # Calculate simple sentiment score
    total_words = len(text_lower.split())
    if total_words == 0:
        return 0.0
        
    sentiment = (positive_count - negative_count) / max(total_words, 1)
    return max(-1.0, min(1.0, sentiment * 5))  # Scale and clamp


def get_sentiment_label(score):
    """Convert sentiment score to readable label"""
    if score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"


def get_bias_score(bias_type):
    """Convert bias category to numerical score for plotting"""
    bias_scores = {
        'left': -1,
        'center': 0,
        'right': 1
    }
    return bias_scores.get(bias_type, 0)


def create_bias_spectrum_chart(articles):
    """Create interactive bias spectrum visualization"""
    st.subheader("📊 Bias Spectrum Analysis")
    
    if not articles:
        st.warning("No articles to visualize")
        return
    
    df = pd.DataFrame(articles)
    
    # Enhanced scatter plot with better interactivity
    fig = px.scatter(
        df,
        x='bias_score',
        y='sentiment_score',
        color='bias_category',
        size=[abs(score) * 10 + 8 for score in df['sentiment_score']],  # Better size scaling
        hover_data={
            'source': True,
            'credibility': True,
            'bias_score': False,
            'sentiment_score': ':.3f',
            'bias_category': False
        },
        hover_name='title',
        title="Political Bias vs Sentiment Analysis - Interactive View",
        labels={
            'bias_score': 'Political Bias Spectrum',
            'sentiment_score': 'Sentiment Score',
            'bias_category': 'Source Category'
        },
        color_discrete_map=BIAS_COLORS,
        height=600
    )
    
    # Enhanced customization
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[-1, 0, 1],
            ticktext=['Left-Leaning', 'Center', 'Right-Leaning'],
            range=[-1.5, 1.5],
            title_font_size=14
        ),
        yaxis=dict(
            title='Sentiment Score (Negative ← → Positive)',
            range=[-1.1, 1.1],
            title_font_size=14
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Add quadrant lines and annotations
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dot", line_color="gray", opacity=0.5)
    
    # Add quadrant labels
    fig.add_annotation(x=-0.75, y=0.8, text="Left + Positive", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=0.75, y=0.8, text="Right + Positive", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=-0.75, y=-0.8, text="Left + Negative", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=0.75, y=-0.8, text="Right + Negative", showarrow=False, font=dict(size=10, color="gray"))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Enhanced interpretation with insights
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("📖 How to Read This Chart"):
            st.markdown("""
            **Axes Explained:**
            - **X-Axis**: Political bias from Left (-1) to Right (+1)
            - **Y-Axis**: Sentiment from Negative (-1) to Positive (+1)
            - **Bubble Size**: Larger = stronger sentiment (positive or negative)
            - **Colors**: 🔵 Left, 🟢 Center, 🔴 Right
            """)
    
    with col2:
        with st.expander("🔍 What to Look For"):
            st.markdown("""
            **Key Patterns:**
            - **Clustering**: Do similar sources share sentiment?
            - **Spread**: Wide sentiment range indicates controversy
            - **Outliers**: Sources reporting very differently
            - **Quadrants**: Which political-sentiment combinations appear?
            """)
    
    # Quick insights
    if len(df) > 1:
        left_avg = df[df['bias_category'] == 'left']['sentiment_score'].mean() if len(df[df['bias_category'] == 'left']) > 0 else 0
        right_avg = df[df['bias_category'] == 'right']['sentiment_score'].mean() if len(df[df['bias_category'] == 'right']) > 0 else 0
        center_avg = df[df['bias_category'] == 'center']['sentiment_score'].mean() if len(df[df['bias_category'] == 'center']) > 0 else 0
        
        if abs(left_avg - right_avg) > 0.3:
            st.info(f"🎯 **Bias Alert**: Significant sentiment difference detected between left ({left_avg:.2f}) and right ({right_avg:.2f}) sources!")
        elif abs(max(left_avg, right_avg, center_avg) - min(left_avg, right_avg, center_avg)) < 0.2:
            st.success("✅ **Consensus Found**: Most sources show similar sentiment about this topic!")
        else:
            st.warning("⚖️ **Mixed Coverage**: Sources show varied sentiment - consider multiple perspectives!")


def create_side_by_side_comparison(articles):
    """Create side-by-side comparison of articles"""
    st.subheader("🔄 Side-by-Side Source Comparison")
    
    if not articles:
        st.warning("No articles to compare")
        return
    
    # Group articles by bias category
    articles_by_bias = defaultdict(list)
    for article in articles:
        articles_by_bias[article['bias_category']].append(article)
    
    # Create comparison tabs
    tabs = st.tabs(["📰 Headlines", "😊 Sentiment", "🏛️ Credibility", "📋 Full Comparison"])
    
    with tabs[0]:  # Headlines comparison
        st.write("**Compare how different sources frame the same story:**")
        
        for bias_type in ['left', 'center', 'right']:
            if articles_by_bias[bias_type]:
                st.markdown(f"### {bias_type.title()} Sources")
                for article in articles_by_bias[bias_type]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{article['source']}**: {article['title']}")
                    with col2:
                        sentiment_emoji = get_sentiment_emoji(article['sentiment_label'])
                        st.markdown(f"{sentiment_emoji} {article['sentiment_label']}")
                st.divider()
    
    with tabs[1]:  # Sentiment comparison
        st.write("**Sentiment analysis across the political spectrum:**")
        
        sentiment_data = []
        for article in articles:
            sentiment_data.append({
                'Source': article['source'],
                'Bias': article['bias_category'].title(),
                'Sentiment Score': article['sentiment_score'],
                'Sentiment': article['sentiment_label']
            })
        
        df_sentiment = pd.DataFrame(sentiment_data)
        
        # Create bar chart
        fig = px.bar(
            df_sentiment,
            x='Source',
            y='Sentiment Score',
            color='Bias',
            color_discrete_map=BIAS_COLORS,
            title="Sentiment Scores by Source"
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:  # Credibility comparison
        st.write("**Source credibility and reliability ratings:**")
        
        credibility_data = defaultdict(list)
        for article in articles:
            credibility_data[article['bias_category']].append({
                'source': article['source'],
                'credibility': article['credibility'],
                'sentiment': article['sentiment_label']
            })
        
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        bias_types = ['left', 'center', 'right']
        
        for i, bias_type in enumerate(bias_types):
            with columns[i]:
                st.markdown(f"**{bias_type.title()} Sources**")
                for article_data in credibility_data[bias_type]:
                    credibility_color = get_credibility_color(article_data['credibility'])
                    st.markdown(f"🔹 **{article_data['source']}**")
                    st.markdown(f"   Credibility: {credibility_color} {article_data['credibility']}")
                    st.markdown(f"   Sentiment: {get_sentiment_emoji(article_data['sentiment'])} {article_data['sentiment']}")
                    st.markdown("---")
    
    with tabs[3]:  # Full comparison
        st.write("**Complete article details:**")
        
        for i, article in enumerate(articles):
            with st.expander(f"{article['source']} - {article['title'][:50]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Title**: {article['title']}")
                    st.markdown(f"**Description**: {article['description']}")
                    st.markdown(f"🔗 [Read Full Article]({article['url']})")
                
                with col2:
                    # Bias indicator
                    bias_color = BIAS_COLORS[article['bias_category']]
                    st.markdown(f"**Political Bias**: <span style='color: {bias_color}'>●</span> {article['bias_category'].title()}", unsafe_allow_html=True)
                    
                    # Sentiment
                    sentiment_emoji = get_sentiment_emoji(article['sentiment_label'])
                    st.markdown(f"**Sentiment**: {sentiment_emoji} {article['sentiment_label']} ({article['sentiment_score']:.3f})")
                    
                    # Credibility
                    credibility_color = get_credibility_color(article['credibility'])
                    st.markdown(f"**Credibility**: {credibility_color} {article['credibility']}")


def analyze_key_differences(articles):
    """Analyze and highlight key differences between sources"""
    st.subheader("💡 Key Differences & Insights")
    
    if not articles:
        st.warning("No articles to analyze")
        return
    
    # Group by bias type
    articles_by_bias = defaultdict(list)
    for article in articles:
        articles_by_bias[article['bias_category']].append(article)
    
    # Analysis tabs
    tabs = st.tabs(["🎯 Bias Patterns", "📊 Sentiment Trends", "🔍 Source Analysis", "💭 Key Insights"])
    
    with tabs[0]:  # Bias patterns
        st.write("**How different political leanings approach this story:**")
        
        bias_analysis = {}
        for bias_type, bias_articles in articles_by_bias.items():
            if bias_articles:
                avg_sentiment = sum(a['sentiment_score'] for a in bias_articles) / len(bias_articles)
                common_words = extract_common_words([a['title'] + ' ' + a['description'] for a in bias_articles])
                
                bias_analysis[bias_type] = {
                    'article_count': len(bias_articles),
                    'avg_sentiment': avg_sentiment,
                    'common_words': common_words,
                    'sources': [a['source'] for a in bias_articles]
                }
        
        for bias_type, analysis in bias_analysis.items():
            st.markdown(f"### {bias_type.title()}-leaning Sources")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Articles Found", analysis['article_count'])
            with col2:
                sentiment_direction = "📈 Positive" if analysis['avg_sentiment'] > 0 else "📉 Negative" if analysis['avg_sentiment'] < 0 else "➡️ Neutral"
                st.metric("Avg Sentiment", f"{analysis['avg_sentiment']:.3f}", sentiment_direction)
            with col3:
                st.metric("Sources", len(analysis['sources']))
            
            if analysis['common_words']:
                st.markdown(f"**Common themes**: {', '.join(analysis['common_words'][:5])}")
            
            st.divider()
    
    with tabs[1]:  # Sentiment trends
        st.write("**Sentiment comparison across political spectrum:**")
        
        # Create sentiment comparison chart
        sentiment_summary = []
        for bias_type, bias_articles in articles_by_bias.items():
            if bias_articles:
                sentiments = [a['sentiment_score'] for a in bias_articles]
                sentiment_summary.append({
                    'Bias Category': bias_type.title(),
                    'Average Sentiment': sum(sentiments) / len(sentiments),
                    'Sentiment Range': max(sentiments) - min(sentiments),
                    'Article Count': len(bias_articles)
                })
        
        if sentiment_summary:
            df_summary = pd.DataFrame(sentiment_summary)
            
            fig = px.bar(
                df_summary,
                x='Bias Category',
                y='Average Sentiment',
                color='Bias Category',
                color_discrete_map={'Left': BIAS_COLORS['left'], 'Center': BIAS_COLORS['center'], 'Right': BIAS_COLORS['right']},
                title="Average Sentiment by Political Bias"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            max_sentiment = df_summary.loc[df_summary['Average Sentiment'].idxmax()]
            min_sentiment = df_summary.loc[df_summary['Average Sentiment'].idxmin()]
            
            st.info(f"📊 **Sentiment Insights**: {max_sentiment['Bias Category']} sources are most positive ({max_sentiment['Average Sentiment']:.3f}), while {min_sentiment['Bias Category']} sources are most negative ({min_sentiment['Average Sentiment']:.3f})")
    
    with tabs[2]:  # Source analysis
        st.write("**Individual source performance and credibility:**")
        
        source_data = []
        for article in articles:
            source_data.append({
                'Source': article['source'],
                'Political Bias': article['bias_category'].title(),
                'Sentiment Score': article['sentiment_score'],
                'Credibility': article['credibility'],
                'URL': article['url']
            })
        
        df_sources = pd.DataFrame(source_data)
        st.dataframe(df_sources, use_container_width=True)
        
        # Source insights with better handling
        if len(df_sources) > 1:
            max_sentiment = df_sources['Sentiment Score'].max()
            min_sentiment = df_sources['Sentiment Score'].min()
            
            # Only show insights if there's actual variation in sentiment
            if abs(max_sentiment - min_sentiment) > 0.001:  # Small threshold for floating point comparison
                most_positive = df_sources.loc[df_sources['Sentiment Score'].idxmax()]
                most_negative = df_sources.loc[df_sources['Sentiment Score'].idxmin()]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"📈 **Most Positive**: {most_positive['Source']} ({most_positive['Sentiment Score']:.3f})")
                with col2:
                    st.error(f"📉 **Most Negative**: {most_negative['Source']} ({most_negative['Sentiment Score']:.3f})")
            else:
                st.info("📊 **Note**: All sources show similar sentiment scores for this topic - this could indicate broad consensus or neutral reporting.")
    
    with tabs[3]:  # Key insights
        st.write("**Summary of bias patterns and media landscape insights:**")
        
        # Generate insights
        total_articles = len(articles)
        bias_distribution = {bias: len([a for a in articles if a['bias_category'] == bias]) for bias in ['left', 'center', 'right']}
        avg_sentiment_overall = sum(a['sentiment_score'] for a in articles) / total_articles if total_articles > 0 else 0
        
        # Key insights
        insights = generate_key_insights(articles, bias_distribution, avg_sentiment_overall)
        
        for i, insight in enumerate(insights, 1):
            st.markdown(f"**{i}.** {insight}")
            
        # Recommendations
        st.markdown("### 🎯 Recommendations for Critical News Consumption:")
        recommendations = [
            "📚 **Read multiple sources** from different political perspectives before forming opinions",
            "🧐 **Pay attention to language choices** - emotional words may indicate bias",
            "📊 **Consider the sentiment** - extremely positive or negative coverage may be biased",
            "🏛️ **Check source credibility** - some sources are more reliable than others",
            "🔍 **Look for missing information** - what story elements are some sources not covering?",
            "⚖️ **Seek balance** - truth often lies between extreme positions"
        ]
        
        for recommendation in recommendations:
            st.markdown(f"- {recommendation}")


def extract_common_words(texts, min_length=4):
    """Extract common meaningful words from a list of texts"""
    if not texts:
        return []
    
    import re
    from collections import Counter
    
    # Common stop words to exclude
    stop_words = set(['this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'their', 'said', 'each', 'which', 'them', 'were', 'says', 'more', 'news', 'after', 'about'])
    
    all_words = []
    for text in texts:
        # Extract words, convert to lowercase, filter by length and stop words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        filtered_words = [word for word in words if len(word) >= min_length and word not in stop_words]
        all_words.extend(filtered_words)
    
    # Return most common words
    word_counts = Counter(all_words)
    return [word for word, count in word_counts.most_common(10)]


def generate_key_insights(articles, bias_distribution, avg_sentiment):
    """Generate key insights from the analysis"""
    insights = []
    
    # Coverage distribution insight
    max_bias = max(bias_distribution, key=bias_distribution.get)
    min_bias = min(bias_distribution, key=bias_distribution.get)
    
    if bias_distribution[max_bias] > bias_distribution[min_bias]:
        insights.append(f"📊 **Coverage imbalance detected**: {max_bias.title()} sources provided {bias_distribution[max_bias]} articles vs {min_bias.title()} sources with {bias_distribution[min_bias]} articles")
    
    # Sentiment insight
    if avg_sentiment > 0.2:
        insights.append(f"😊 **Overall positive coverage** with average sentiment of {avg_sentiment:.3f} - this story is generally reported favorably across sources")
    elif avg_sentiment < -0.2:
        insights.append(f"😞 **Overall negative coverage** with average sentiment of {avg_sentiment:.3f} - this story generates negative reactions across the political spectrum")
    else:
        insights.append(f"😐 **Neutral coverage** with average sentiment of {avg_sentiment:.3f} - sources are reporting factually without strong emotional language")
    
    # Bias pattern insight
    sentiments_by_bias = {}
    for bias in ['left', 'center', 'right']:
        bias_articles = [a for a in articles if a['bias_category'] == bias]
        if bias_articles:
            sentiments_by_bias[bias] = sum(a['sentiment_score'] for a in bias_articles) / len(bias_articles)
    
    if len(sentiments_by_bias) >= 2:
        max_sentiment_bias = max(sentiments_by_bias, key=sentiments_by_bias.get)
        min_sentiment_bias = min(sentiments_by_bias, key=sentiments_by_bias.get)
        
        if abs(sentiments_by_bias[max_sentiment_bias] - sentiments_by_bias[min_sentiment_bias]) > 0.3:
            insights.append(f"⚖️ **Significant bias detected**: {max_sentiment_bias.title()} sources are more positive ({sentiments_by_bias[max_sentiment_bias]:.3f}) than {min_sentiment_bias.title()} sources ({sentiments_by_bias[min_sentiment_bias]:.3f})")
    
    # Add general insight about media literacy
    insights.append(f"🎓 **Media literacy reminder**: These {len(articles)} articles show how the same event can be framed differently - always consider multiple perspectives for a complete picture")
    
    return insights


def get_sentiment_emoji(sentiment_label):
    """Get emoji for sentiment label"""
    emoji_map = {
        'Positive': '😊',
        'Neutral': '😐',
        'Negative': '😞'
    }
    return emoji_map.get(sentiment_label, '😐')


def get_credibility_color(credibility):
    """Get color indicator for credibility"""
    color_map = {
        'High': '🟢',
        'Medium': '🟡',
        'Low': '🔴',
        'Unknown': '⚪'
    }
    return color_map.get(credibility, '⚪')


def run_news_perspective_analyzer_feature(*args, **kwargs):
    """Wrapper function to match expected interface"""
    render_news_perspective_analyzer()


if __name__ == "__main__":
    run_news_perspective_analyzer_feature()