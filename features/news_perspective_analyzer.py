""""""

News Perspective Analyzer - REMOVEDNews Perspective Analyzer - Compare how different news sources with varying political biases report the same story

"""

This feature has been removed from the application. The module is kept as a

minimal placeholder to avoid accidental direct imports. Use the main appimport streamlit as st

routing and `features` package exports to control available features.import requests

"""import pandas as pd

import plotly.express as px

from datetime import datetime, timedelta

def run_news_perspective_analyzer_feature(*args, **kwargs):from collections import defaultdict

    """Placeholder: feature removed"""import re

    raise RuntimeError("News Perspective Analyzer has been removed from this build.")from collections import Counter


from utils.helpers import get_secret_or_env
try:
    from utils.models import analyze_sentiment
except ImportError:
    # Fallback if models import fails
    def analyze_sentiment(text):
        return 0.0, 'neutral'

try:
    from utils.source_data import get_source_political_leaning
except ImportError:
    # Fallback if source_data import fails
    def get_source_political_leaning(url):
        return 'center'

# Bias color mapping
BIAS_COLORS = {
    'left': '#4285F4',     # Blue
    'center': '#34A853',   # Green  
    'right': '#EA4335'     # Red
}

def render_news_perspective_analyzer():
    """Main render function for News Perspective Analyzer"""
    st.title("News Perspective Analyzer")
    st.markdown("Compare how different news sources with varying political biases report the same story")
    
    # Main interface
    with st.form("perspective_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            topic = st.text_input(
                "Enter a news topic to analyze:",
                placeholder="e.g., Biden economy, Trump trial, climate change",
                help="Enter any current news topic to see how different political perspectives cover it"
            )
        
        with col2:
            submitted = st.form_submit_button("Analyze Perspectives", type="primary")
    
    if submitted and topic:
        analyze_news_perspective(topic)
    elif submitted and not topic:
        st.error("Please enter a topic to analyze")


def analyze_news_perspective(topic):
    """Analyze news perspective across political spectrum"""
    with st.spinner("Analyzing perspectives..."):
        # Collect articles from different bias categories
        articles_by_bias = collect_multi_source_articles(topic)
        
        # Combine all articles and analyze
        all_articles = []
        for bias_articles in articles_by_bias.values():
            all_articles.extend(bias_articles)
        
        if not all_articles:
            st.error("No articles found for this topic. Try a different search term.")
            return
        
        # Analyze sentiment and bias
        analyzed_articles = analyze_articles_sentiment_bias(articles_by_bias)
        
        # Display results
        bias_categories_found = len([bias for bias, articles in articles_by_bias.items() if articles])
        
        # Show visualizations and comparisons
        create_bias_spectrum_chart(analyzed_articles)
        create_side_by_side_comparison(analyzed_articles)
        analyze_key_differences(analyzed_articles)
        
        # Success message
        st.success(f"Analysis complete! Found {len(analyzed_articles)} articles across {bias_categories_found} perspectives.")


def collect_multi_source_articles(topic, max_per_bias=2):
    """Collect articles from different bias categories"""
    api_key = get_secret_or_env("NEWS_API_KEY")
    articles_by_bias = {'left': [], 'center': [], 'right': []}
    
    if not api_key:
        st.error("News API key not configured. Please check your environment settings.")
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
            st.warning("No articles found for this topic from News API")
            progress_bar.empty()
            progress_text.empty()
            return articles_by_bias
        
        progress_text.text("Sorting articles by political bias...")
        
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
            st.success(f"Found {total_articles} articles across different perspectives")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Left-leaning", len(articles_by_bias['left']))
            with col2:
                st.metric("Center", len(articles_by_bias['center']))
            with col3:
                st.metric("Right-leaning", len(articles_by_bias['right']))
        else:
            st.warning("Could not categorize articles by political bias. Try a different topic.")
        
        return articles_by_bias
        
    except requests.RequestException as e:
        st.error(f"Network error: {str(e)}")
        progress_bar.empty()
        progress_text.empty()
        return articles_by_bias
    except Exception as e:
        st.error(f"Error collecting articles: {str(e)}")
        progress_bar.empty()
        progress_text.empty()
        return articles_by_bias


def determine_source_bias(source_name, article_url):
    """Determine political bias using the actual source database"""
    # Extract domain from URL for lookup
    domain = ""
    if article_url:
        try:
            from urllib.parse import urlparse
            domain = urlparse(article_url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
        except:
            pass
    
    # Use the actual source database
    political_leaning = get_source_political_leaning(domain)
    
    if political_leaning:
        if political_leaning == 'left-leaning':
            return 'left'
        elif political_leaning == 'right-leaning':
            return 'right'
        elif political_leaning == 'center':
            return 'center'
    
    return None


def process_article(article, bias_type):
    """Process and validate article data"""
    try:
        title = article.get('title', '').strip()
        description = article.get('description', '').strip()
        
        if not title or title == '[Removed]' or not description or description == '[Removed]':
            return None
        
        return {
            'title': title,
            'description': description,
            'url': article.get('url', ''),
            'source': article.get('source', {}).get('name', 'Unknown'),
            'bias_category': bias_type,
            'published_at': article.get('publishedAt', ''),
            'credibility': 'Medium'  # Default credibility
        }
    except Exception:
        return None


def analyze_articles_sentiment_bias(articles_by_bias):
    """Analyze sentiment and bias for all articles"""
    analyzed_articles = []
    
    progress_bar = st.progress(0)
    progress_text = st.empty()
    total_articles = sum(len(articles) for articles in articles_by_bias.values())
    processed = 0
    
    for bias_category, articles in articles_by_bias.items():
        for article in articles:
            progress_text.text(f"Analyzing sentiment for {article['source']}...")
            
            # Analyze sentiment
            text_to_analyze = f"{article['title']} {article['description']}"
            sentiment_result = analyze_sentiment_with_fallback(text_to_analyze)
            
            # Add analysis results
            article.update({
                'sentiment_score': sentiment_result.get('compound', 0),
                'sentiment_label': get_sentiment_label(sentiment_result.get('compound', 0)),
                'bias_score': get_bias_score(bias_category)
            })
            
            analyzed_articles.append(article)
            processed += 1
            progress_bar.progress(processed / total_articles)
    
    progress_bar.empty()
    progress_text.empty()
    
    return analyzed_articles


def analyze_sentiment_with_fallback(text):
    """Analyze sentiment with fallback methods"""
    try:
        # Try main sentiment analysis
        result = analyze_sentiment(text)
        
        # Validate result
        if isinstance(result, dict) and 'compound' in result:
            return result
        else:
            # Fallback to simple analysis
            return simple_sentiment_analysis(text)
    except Exception:
        # Fallback to simple analysis
        return simple_sentiment_analysis(text)


def simple_sentiment_analysis(text):
    """Simple sentiment analysis fallback"""
    positive_words = set(['good', 'great', 'excellent', 'positive', 'success', 'win', 'victory', 'achieve', 'improve', 'benefit', 'strong', 'effective', 'progress', 'growth', 'increase', 'rise', 'gain', 'advance', 'breakthrough', 'solution'])
    negative_words = set(['bad', 'terrible', 'negative', 'fail', 'failure', 'lose', 'loss', 'problem', 'issue', 'concern', 'crisis', 'decline', 'decrease', 'fall', 'drop', 'threat', 'risk', 'danger', 'difficult', 'challenge'])
    
    text_lower = text.lower()
    words = set(text_lower.split())
    
    positive_count = len(words.intersection(positive_words))
    negative_count = len(words.intersection(negative_words))
    
    if positive_count > negative_count:
        sentiment_score = min(0.5, positive_count * 0.1)
    elif negative_count > positive_count:
        sentiment_score = max(-0.5, -negative_count * 0.1)
    else:
        sentiment_score = 0.0
    
    return {
        'compound': sentiment_score,
        'pos': max(0, sentiment_score),
        'neu': 1 - abs(sentiment_score),
        'neg': max(0, -sentiment_score)
    }


def get_sentiment_label(score):
    """Get sentiment label from score"""
    if score > 0.1:
        return 'Positive'
    elif score < -0.1:
        return 'Negative'
    else:
        return 'Neutral'


def get_bias_score(bias_type):
    """Convert bias category to numerical score"""
    bias_scores = {'left': -1, 'center': 0, 'right': 1}
    return bias_scores.get(bias_type, 0)


def create_bias_spectrum_chart(articles):
    """Create bias vs sentiment chart"""
    st.subheader("Bias vs Sentiment Analysis")
    
    if not articles:
        st.warning("No articles to visualize")
        return
    
    df = pd.DataFrame(articles)
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='bias_score',
        y='sentiment_score',
        color='bias_category',
        size=[abs(score) * 10 + 8 for score in df['sentiment_score']],
        """
        News Perspective Analyzer - REMOVED

        This feature has been removed from the application. The module is kept as a
        minimal placeholder to avoid accidental direct imports. Use the main app
        routing and `features` package exports to control available features.
        """

        def run_news_perspective_analyzer_feature(*args, **kwargs):
            raise RuntimeError("News Perspective Analyzer has been removed from this build.")

    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dot", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Quick insights
    if len(df) > 1:
        left_avg = df[df['bias_category'] == 'left']['sentiment_score'].mean() if len(df[df['bias_category'] == 'left']) > 0 else 0
        right_avg = df[df['bias_category'] == 'right']['sentiment_score'].mean() if len(df[df['bias_category'] == 'right']) > 0 else 0
        
        if abs(left_avg - right_avg) > 0.3:
            st.info(f"**Different viewpoints detected**: Left sources avg {left_avg:.2f}, Right sources avg {right_avg:.2f}")
        elif abs(left_avg - right_avg) < 0.2:
            st.success("**Similar coverage**: Most sources agree on this topic")
        else:
            st.warning("**Mixed coverage**: Sources show varied perspectives")


def create_side_by_side_comparison(articles):
    """Create side-by-side comparison of articles"""
    st.subheader("Source Comparison")
    
    if not articles:
        st.warning("No articles to compare")
        return
    
    # Group articles by bias category
    articles_by_bias = defaultdict(list)
    for article in articles:
        articles_by_bias[article['bias_category']].append(article)
    
    # Create comparison sections
    tabs = st.tabs(["Headlines", "Sentiment", "Details"])
    
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
                        st.markdown(f"{article['sentiment_label']} ({article['sentiment_score']:.2f})")
                st.divider()
    
    with tabs[1]:  # Sentiment comparison
        st.write("**Sentiment analysis by source:**")
        
        sentiment_data = []
        for article in articles:
            sentiment_data.append({
                'Source': article['source'],
                'Bias': article['bias_category'].title(),
                'Sentiment Score': article['sentiment_score'],
            })
        
        df_sentiment = pd.DataFrame(sentiment_data)
        
        # Create bar chart
        fig = px.bar(
            df_sentiment,
            x='Source',
            y='Sentiment Score',
            color='Bias',
            color_discrete_map=BIAS_COLORS,
            title="Sentiment by Source"
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tabs[2]:  # Details
        st.write("**Complete article details:**")
        
        for article in articles:
            with st.expander(f"{article['source']} - {article['title'][:50]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Title**: {article['title']}")
                    if article.get('description'):
                        st.markdown(f"**Description**: {article['description']}")
                    st.markdown(f"[Read Full Article]({article['url']})")
                
                with col2:
                    st.markdown(f"**Bias**: {article['bias_category'].title()}")
                    st.markdown(f"**Sentiment**: {article['sentiment_label']} ({article['sentiment_score']:.2f})")
                    st.markdown(f"**Credibility**: {article['credibility']}")


def analyze_key_differences(articles):
    """Analyze and highlight key differences between sources"""
    st.subheader("Key Insights")
    
    if not articles:
        st.warning("No articles to analyze")
        return
    
    # Group by bias type
    articles_by_bias = defaultdict(list)
    for article in articles:
        articles_by_bias[article['bias_category']].append(article)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(articles))
    
    with col2:
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)
        st.metric("Average Sentiment", f"{avg_sentiment:.2f}")
    
    with col3:
        unique_sources = len(set(a['source'] for a in articles))
        st.metric("Unique Sources", unique_sources)
    
    # Coverage by bias
    st.subheader("Coverage Distribution")
    
    bias_stats = []
    for bias_type in ['left', 'center', 'right']:
        articles_count = len(articles_by_bias[bias_type])
        if articles_count > 0:
            avg_sentiment = sum(a['sentiment_score'] for a in articles_by_bias[bias_type]) / articles_count
            sources = ', '.join(set(a['source'] for a in articles_by_bias[bias_type]))
            bias_stats.append({
                'Political Leaning': bias_type.title(),
                'Articles': articles_count,
                'Avg Sentiment': f"{avg_sentiment:.2f}",
                'Sources': sources
            })
    
    if bias_stats:
        df_stats = pd.DataFrame(bias_stats)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    
    # Key observations
    st.subheader("Key Observations")
    
    insights = []
    
    # Coverage balance
    coverage_counts = {bias: len(articles_by_bias[bias]) for bias in ['left', 'center', 'right']}
    max_coverage = max(coverage_counts.values())
    min_coverage = min(coverage_counts.values())
    
    if max_coverage > min_coverage:
        max_bias = max(coverage_counts, key=coverage_counts.get)
        insights.append(f"Most coverage from {max_bias} sources ({max_coverage} articles)")
    
    # Overall sentiment
    if avg_sentiment > 0.2:
        insights.append("Generally positive coverage across sources")
    elif avg_sentiment < -0.2:
        insights.append("Generally negative coverage across sources")
    else:
        insights.append("Mostly neutral coverage")
    
    # Display insights
    for insight in insights:
        st.info(f"• {insight}")
    
    # Reading tips
    with st.expander("Tips for Balanced Reading"):
        st.markdown("""
        **For a complete picture:**
        - Compare articles from different political perspectives
        - Notice differences in language and tone
        - Consider source credibility
        - Look for facts vs opinions
        - Identify what stories might be missing
        """)


def run_news_perspective_analyzer_feature(*args, **kwargs):
    """Wrapper function to match expected interface"""
    render_news_perspective_analyzer()


if __name__ == "__main__":
    run_news_perspective_analyzer_feature()