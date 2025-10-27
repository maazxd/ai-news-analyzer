"""
Additional helper functions for features
"""
import requests
import streamlit as st


@st.cache_data(show_spinner=False)
def fetch_similar_articles(query, api_key, num_results=5):
    """Fetch similar articles from NewsAPI"""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": num_results,
        "sortBy": "relevancy",
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    articles = []
    if data.get("status") == "ok":
        for article in data.get("articles", []):
            articles.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "source": article["source"].get("name", "")
            })
    return articles


def generate_insight(text, summarize_text_func=None, load_insight_model_func=None):
    """Generate AI insight from news text with comprehensive fallback analysis"""
    
    # Always try rule-based analysis as it's more reliable
    rule_based_insight = generate_rule_based_insight(text)
    
    # Try to enhance with AI if available
    try:
        if load_insight_model_func:
            # Load model with error handling
            insight_model = load_insight_model_func()
            if insight_model is None:
                return rule_based_insight
            
            # Prepare text (limit length for processing)
            if len(text.split()) > 300:
                # Use first few sentences instead of summary to avoid errors
                sentences = text.split('.')[:5]
                summary = '. '.join(sentences) + '.'
            else:
                summary = text
            
            # Create focused prompt
            prompt = f"Summarize the key points and potential concerns about this news: {summary[:500]}"
            
            # Generate with conservative parameters
            try:
                if hasattr(insight_model, 'task') and 'summarization' in insight_model.task:
                    # If it's a summarization model, use it differently
                    result = insight_model(summary[:1000], max_length=100, min_length=20)
                    ai_insight = result[0]['summary_text'] if result else ""
                else:
                    # Text generation model
                    result = insight_model(prompt, max_length=120, do_sample=False)
                    ai_insight = result[0]['generated_text'].replace(prompt, "").strip() if result else ""
                
                # Combine AI insight with rule-based analysis
                if ai_insight and len(ai_insight) > 15:
                    return f"{ai_insight} {rule_based_insight}"
            
            except Exception as inner_e:
                print(f"Model inference failed: {inner_e}")
                return rule_based_insight
    
    except Exception as e:
        print(f"AI insight generation failed: {e}")
    
    return rule_based_insight


def generate_rule_based_insight(text):
    """Generate insight using rule-based analysis when AI models fail"""
    import re
    
    insights = []
    text_lower = text.lower()
    
    # Analyze article characteristics
    word_count = len(text.split())
    sentence_count = len(re.findall(r'[.!?]+', text))
    avg_sentence_length = word_count / max(sentence_count, 1)
    
    # Check for key content indicators
    has_quotes = '"' in text or "'" in text
    has_numbers = bool(re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text))
    has_sources = any(phrase in text_lower for phrase in 
                     ['according to', 'sources say', 'reported by', 'study shows'])
    
    # Generate insights based on analysis
    if word_count < 100:
        insights.append("This appears to be a brief news item or headline.")
    elif word_count > 800:
        insights.append("This is a comprehensive article with detailed coverage.")
    
    if has_quotes:
        insights.append("The article includes direct quotes, which adds credibility.")
    
    if has_sources:
        insights.append("Multiple sources or attributions are mentioned.")
    
    if has_numbers:
        insights.append("Contains statistical or numerical data that can be verified.")
    
    # Check for potential bias indicators
    emotional_words = ['shocking', 'amazing', 'unbelievable', 'outrageous', 'devastating']
    if any(word in text_lower for word in emotional_words):
        insights.append("Uses emotionally charged language - consider checking for bias.")
    
    # Check for uncertainty language
    uncertain_words = ['allegedly', 'reportedly', 'sources claim', 'rumored']
    if any(phrase in text_lower for phrase in uncertain_words):
        insights.append("Contains unverified claims that require further confirmation.")
    
    # Combine insights or provide default
    if insights:
        return " ".join(insights[:3])  # Limit to top 3 insights
    else:
        return "This article covers a news topic. Consider checking multiple sources for complete context and verification of claims."
    return insight
