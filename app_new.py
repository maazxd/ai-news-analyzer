
import streamlit as st
import joblib
from nltk.corpus import stopwords
from langdetect import DetectorFactory

# Import utilities
from utils import (
    FEATURE_ICONS, CUSTOM_CSS, preprocess,
    load_fake_news_model, fetch_article_text
)

# Import core feature modules
from features import (
    run_paste_news_feature,
    run_fetch_news_feature,
    run_summarize_feature,
    run_summarize_link_feature,
    run_geographic_news_map_feature,
    run_ai_insight_feature,
    run_translate_feature,
    run_credibility_feature
)


st.set_page_config(
    page_title="News Analysis",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "News Analysis - A comprehensive tool for news verification and media analysis."
    }
)

# ========== APPLY CUSTOM CSS ==========
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========== INITIALIZATION ==========
DetectorFactory.seed = 0  # for consistent language detection

# Load stopwords
def _load_stop_words():
    """
    Try NLTK stopwords first; if it fails due to missing data or loader bugs,
    fall back to scikit‑learn's built-in English stopword list.
    """
    try:
        return set(stopwords.words('english'))
    except Exception:
        try:
            from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
            return set(ENGLISH_STOP_WORDS)
        except Exception:
            return set()

stop_words = _load_stop_words()

# Load ML model and vectorizer
vectorizer, model = load_fake_news_model()

# ========== SIDEBAR ==========
st.sidebar.markdown(
    """
    <div class='sidebar-header'>
        <h2 style='margin:0; font-size:1.6em; font-weight:500;'>📰 News Hub</h2>
    
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# Feature selector with icons
choice = st.sidebar.selectbox(
    "Choose Feature",
    list(FEATURE_ICONS.keys()),
    format_func=lambda x: f"{FEATURE_ICONS[x]} {x}",
    index=0
)

# Footer
st.sidebar.markdown(
    """
    <div style='text-align:center; padding:0.8rem 0; font-size:0.8em; opacity:0.7;'>
    
        
    </div>
    """,
    unsafe_allow_html=True
)

# ========== FEATURE ROUTING ==========
if choice == "News Verification":
    run_paste_news_feature(model, vectorizer, stop_words, preprocess, fetch_article_text)

elif choice == "Live News Feed":
    run_fetch_news_feature()

elif choice == "Article Summary":
    run_summarize_feature()

elif choice == "URL Analysis":
    run_summarize_link_feature(fetch_article_text)

elif choice == "Geographic News Map":
    run_geographic_news_map_feature()

elif choice == "Translation":
    run_translate_feature(fetch_article_text)

elif choice == "Source Checker":
     run_credibility_feature()
