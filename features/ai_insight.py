
import streamlit as st
from utils.helpers import get_secret_or_env, detect_language
from utils.models import analyze_sentiment, extract_entities
from utils.helpers import detect_bias_signals
from utils.source_data import get_source_credibility, get_source_political_leaning
from utils.news_helpers import fetch_similar_articles, generate_insight
from utils.models import summarize_text, load_insight_model


def run_ai_insight_feature():
    """Deep Analysis - Comprehensive news article analysis"""
    
    st.subheader("AI NEWS INSIGHT")
    st.write("Get comprehensive analysis and insights from news articles")
    
    news = st.text_area(
        "Article Text:", 
        height=200,
        placeholder="Paste the news article content here for detailed analysis..."
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        src_url_opt = st.text_input("Source URL (optional)", placeholder="https://example.com/article")
    with col2:
        show_corroboration = st.checkbox("Find Similar Coverage", value=True)




    NEWS_API_KEY = get_secret_or_env("NEWS_API_KEY")

    if st.button("Analyze Article", use_container_width=True):
        if not news.strip():
            st.warning("Please enter article text to analyze.")
            return
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1) Basic Analysis (always works)
            status_text.text("Step 1: Analyzing basic content...")
            progress_bar.progress(25)
            
            word_count = len(news.split())
            sentence_count = len(news.split('.'))
            has_quotes = '"' in news or "'" in news
            
            st.markdown(" Content Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("Word Count", word_count)
            col2.metric("Sentences", sentence_count)
            col3.metric("Has Quotes", "Yes" if has_quotes else "No")
            
            # 2) AI Analysis (with fallback)
            status_text.text("Step 2/4: Generating AI insights...")
            progress_bar.progress(50)
            
            try:
                insight = generate_insight(news, summarize_text, load_insight_model)
                if insight and len(insight) > 20:
                    st.markdown("### AI Insights")
                    st.write(insight)
                else:
                    raise Exception("AI insight generation returned empty result")
            except Exception as e:
                st.markdown("Analysis Summary")
                # Fallback analysis
                if word_count < 100:
                    st.write("⚠️ This appears to be a brief news snippet. Consider checking the full article for complete context.")
                elif word_count > 1000:
                    st.write("📄 This is a comprehensive article with detailed coverage. Key claims should be verified with multiple sources.")
                else:
                    st.write("📝 This article covers a news topic. Cross-reference key facts with reliable sources for verification.")
                
                if has_quotes:
                    st.write("✅ The article includes direct quotes, which generally adds credibility.")
                
                st.caption(f"Note: Advanced AI analysis unavailable ({str(e)[:50]}...)")

            # 3) Content Metrics
            status_text.text("Step 3/4: Analyzing content metrics...")
            progress_bar.progress(75)
            
            st.markdown("### Content Metrics")
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            # Sentiment Analysis (with fallback)
            try:
                sentiment = analyze_sentiment(news)
                metrics_col1.metric("Sentiment", sentiment)
            except:
                # Simple fallback sentiment
                positive_words = ['good', 'positive', 'success', 'achieve', 'win', 'progress']
                negative_words = ['bad', 'negative', 'fail', 'lose', 'crisis', 'problem', 'death', 'disaster']
                
                news_lower = news.lower()
                pos_count = sum(1 for word in positive_words if word in news_lower)
                neg_count = sum(1 for word in negative_words if word in news_lower)
                
                if pos_count > neg_count:
                    sentiment = "Positive"
                elif neg_count > pos_count:
                    sentiment = "Negative"
                else:
                    sentiment = "Neutral"
                metrics_col1.metric("Sentiment", sentiment)
            
            # Language Detection (with fallback)
        
            
            # Bias Detection (with fallback)
            try:
                bias_score, bias_terms = detect_bias_signals(news)
                metrics_col3.metric("Bias Level", f"{bias_score}/100")
            except:
                # Simple bias check
                bias_words = ['shocking', 'unbelievable', 'amazing', 'terrible', 'incredible']
                bias_count = sum(1 for word in bias_words if word.lower() in news.lower())
                simple_bias = min(bias_count * 20, 100)
                metrics_col3.metric("Bias Level", f"{simple_bias}/100")

            # 4) Source Analysis (if URL provided)
            if src_url_opt.strip():
                st.markdown("### Source Analysis")
                try:
                    cred_label, cred_desc = get_source_credibility(src_url_opt)
                    lean_label = get_source_political_leaning(src_url_opt)
                    
                    source_col1, source_col2 = st.columns(2)
                    source_col1.metric("Credibility", cred_label)
                    source_col2.metric("Political Leaning", lean_label.capitalize() if lean_label != 'unknown' else 'Unknown')
                    
                    if cred_desc:
                        st.caption(cred_desc)
                except Exception as e:
                    st.caption(f"Could not analyze source: {e}")

            # 5) Similar Coverage (if enabled)
            status_text.text("Step 4/4: Finding similar coverage...")
            progress_bar.progress(100)
            
            if show_corroboration:
                with st.expander("🔍 Similar Coverage from Other Sources"):
                    query = news.split(".")[0][:120]  # Use first sentence
                    if len(query) < 10:
                        st.caption("Article too short for similarity search.")
                    else:
                        try:
                            similar_articles = fetch_similar_articles(query, NEWS_API_KEY, num_results=5)
                            
                            if not similar_articles:
                                st.caption("No similar coverage found in recent news.")
                            else:
                                st.write(f"Found {len(similar_articles)} related articles:")
                                
                                for i, article in enumerate(similar_articles, 1):
                                    title = article.get('title', 'Unknown Title')
                                    source = article.get('source', 'Unknown Source')
                                    url = article.get('url', '#')
                                    
                                    st.markdown(f"{i}. **{title}**")
                                    st.caption(f"Source: {source} • [Read Article]({url})")
                                    
                                    if i < len(similar_articles):
                                        st.markdown("---")
                        
                        except Exception as e:
                            st.caption(f"Could not search for similar articles: {e}")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.success("Analysis complete!")
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Analysis failed: {str(e)}")
            st.info("Please try again or contact support if the issue persists.")
