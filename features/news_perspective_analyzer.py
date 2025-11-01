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
        
        🔍 **Multi-Source Collection**: Fetches the same story from left-leaning, center, and right-leaning sources
        
        📊 **Bias Spectrum Visualization**: Interactive chart showing political alignment vs sentiment analysis
        
        🔄 **Side-by-Side Comparison**: Headlines, sentiment scores, and credibility ratings compared
        
        💡 **Key Differences Analysis**: Highlights contradictions, common themes, and missing information
        
        🎯 **Educational Value**: Helps users identify bias patterns and think more critically about news consumption
        """)
    
    # Input section
    st.subheader("🔎 Analyze News Coverage")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "Enter a news topic to analyze across the political spectrum:",
            placeholder="e.g., climate summit, election results, economic policy"
        )
    
    with col2:
        analyze_button = st.button("🔍 Analyze Coverage", type="primary")
    
    if analyze_button and topic:
        analyze_news_perspective(topic)
    elif analyze_button and not topic:
        st.warning("⚠️ Please enter a news topic to analyze")


def analyze_news_perspective(topic):
    """Main analysis function that orchestrates the entire perspective analysis"""
    with st.spinner("🔍 Analyzing news coverage across the political spectrum..."):
        # Step 1: Collect articles from different sources
        st.write("📰 **Step 1**: Collecting articles from diverse sources...")
        articles_by_bias = collect_multi_source_articles(topic)
        
        if not any(articles_by_bias.values()):
            st.error("❌ No articles found for this topic. Please try a different search term.")
            return
        
        # Step 2: Analyze sentiment and bias
        st.write("🧠 **Step 2**: Analyzing sentiment and bias patterns...")
        analyzed_articles = analyze_articles_sentiment_bias(articles_by_bias)
        
        # Step 3: Create visualizations
        st.write("📊 **Step 3**: Creating bias spectrum visualization...")
        create_bias_spectrum_chart(analyzed_articles)
        
        # Step 4: Side-by-side comparison
        st.write("🔄 **Step 4**: Generating side-by-side comparison...")
        create_side_by_side_comparison(analyzed_articles)
        
        # Step 5: Key differences analysis
        st.write("💡 **Step 5**: Analyzing key differences and insights...")
        analyze_key_differences(analyzed_articles)


def collect_multi_source_articles(topic, max_per_bias=3):
    """Collect articles from different bias categories"""
    api_key = get_secret_or_env("NEWS_API_KEY")
    articles_by_bias = {'left': [], 'center': [], 'right': []}
    
    if not api_key:
        st.error("❌ News API key not configured. Please check your environment settings.")
        return articles_by_bias
    
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    try:
        total_bias_categories = len(NEWS_SOURCES)
        current_category = 0
        
        for bias_type, sources in NEWS_SOURCES.items():
            progress_text.text(f"Fetching from {bias_type} sources...")
            
            # Search for articles from sources in this bias category
            sources_list = ','.join(sources.keys())
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': topic,
                'sources': sources_list,
                'sortBy': 'publishedAt',
                'pageSize': max_per_bias * 2,  # Get extra to filter
                'language': 'en',
                'apiKey': api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('articles'):
                # Process and filter articles
                for article in data['articles'][:max_per_bias]:
                    processed_article = process_article(article, bias_type)
                    if processed_article:
                        articles_by_bias[bias_type].append(processed_article)
            
            current_category += 1
            progress_bar.progress(current_category / total_bias_categories)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        progress_bar.empty()
        progress_text.empty()
        
        # Display collection summary
        total_articles = sum(len(articles) for articles in articles_by_bias.values())
        if total_articles > 0:
            st.success(f"✅ Successfully collected {total_articles} articles across the political spectrum")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Left-leaning", len(articles_by_bias['left']), delta=None)
            with col2:
                st.metric("Center", len(articles_by_bias['center']), delta=None)
            with col3:
                st.metric("Right-leaning", len(articles_by_bias['right']), delta=None)
        else:
            st.warning("⚠️ No articles found from the specified sources")
        
        return articles_by_bias
        
    except Exception as e:
        st.error(f"❌ Error collecting articles: {str(e)}")
        return articles_by_bias


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
    progress_bar = st.progress(0)
    current_article = 0
    
    for bias_type, articles in articles_by_bias.items():
        for article in articles:
            # Analyze sentiment
            text_for_analysis = f"{article['title']} {article['description']}"
            sentiment_result = analyze_sentiment(text_for_analysis)
            
            # Extract sentiment data
            if isinstance(sentiment_result, dict):
                sentiment_score = sentiment_result.get('compound', 0)
                sentiment_label = get_sentiment_label(sentiment_score)
            else:
                sentiment_score = 0
                sentiment_label = 'Neutral'
            
            # Add analysis results
            article['sentiment_score'] = sentiment_score
            article['sentiment_label'] = sentiment_label
            article['bias_score'] = get_bias_score(bias_type)
            
            analyzed_articles.append(article)
            
            current_article += 1
            progress_bar.progress(current_article / total_articles)
    
    progress_bar.empty()
    return analyzed_articles


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
    
    # Create the scatter plot
    fig = px.scatter(
        df,
        x='bias_score',
        y='sentiment_score',
        color='bias_category',
        size=[abs(score) + 0.5 for score in df['sentiment_score']],  # Size based on sentiment intensity
        hover_data=['source', 'credibility'],
        title="Political Bias vs Sentiment Analysis",
        labels={
            'bias_score': 'Political Bias',
            'sentiment_score': 'Sentiment Score',
            'bias_category': 'Source Type'
        },
        color_discrete_map=BIAS_COLORS
    )
    
    # Customize the chart
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[-1, 0, 1],
            ticktext=['Left-leaning', 'Center', 'Right-leaning'],
            range=[-1.5, 1.5]
        ),
        yaxis=dict(
            title='Sentiment Score',
            range=[-1.1, 1.1]
        ),
        height=500,
        showlegend=True
    )
    
    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dot", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add interpretation
    with st.expander("📖 How to Read This Chart"):
        st.markdown("""
        **X-Axis (Political Bias)**: Left (-1) ← Center (0) → Right (+1)
        
        **Y-Axis (Sentiment)**: Negative (-1) ← Neutral (0) → Positive (+1)
        
        **Bubble Size**: Larger bubbles indicate stronger sentiment (positive or negative)
        
        **Colors**: 🔵 Blue = Left-leaning, 🟢 Green = Center, 🔴 Red = Right-leaning
        
        **Patterns to Look For**:
        - Clustering: Do similar sources have similar sentiment?
        - Spread: How much variation exists across the spectrum?
        - Outliers: Which sources report differently than others in their category?
        """)


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
        
        # Source insights
        if len(df_sources) > 1:
            most_positive = df_sources.loc[df_sources['Sentiment Score'].idxmax()]
            most_negative = df_sources.loc[df_sources['Sentiment Score'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"📈 **Most Positive**: {most_positive['Source']} ({most_positive['Sentiment Score']:.3f})")
            with col2:
                st.error(f"📉 **Most Negative**: {most_negative['Source']} ({most_negative['Sentiment Score']:.3f})")
    
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