"""
Utils package for News Analyzer Platform
"""
from .config import FEATURE_ICONS, CUSTOM_CSS
from .helpers import (
    get_secret_or_env,
    preprocess,
    is_valid_news,
    is_opinion_piece,
    detect_bias_signals,
    detect_language,
    clean_social_text,
    fact_check_claims,
    normalize_factcheck_rating
)
from .models import (
    load_summarizer,
    load_sentiment_analyzer,
    load_insight_model,
    load_ner,
    load_whisper,
    load_zeroshot,
    load_fake_news_model,
    summarize_text,
    analyze_sentiment,
    extract_entities,
    classify_political_leaning_text,
    predict_proba_content_only
)
from .source_data import (
    SOURCE_CREDIBILITY,
    SOURCE_POLITICAL_LEANING,
    get_source_credibility,
    get_source_political_leaning
)
from .article_fetcher import fetch_article_text
from .news_helpers import fetch_similar_articles, generate_insight

__all__ = [
    'FEATURE_ICONS',
    'CUSTOM_CSS',
    'get_secret_or_env',
    'preprocess',
    'is_valid_news',
    'is_opinion_piece',
    'detect_bias_signals',
    'detect_language',
    'clean_social_text',
    'fact_check_claims',
    'normalize_factcheck_rating',
    'load_summarizer',
    'load_sentiment_analyzer',
    'load_insight_model',
    'load_ner',
    'load_whisper',
    'load_zeroshot',
    'load_fake_news_model',
    'summarize_text',
    'analyze_sentiment',
    'extract_entities',
    'classify_political_leaning_text',
    'predict_proba_content_only',
    'SOURCE_CREDIBILITY',
    'SOURCE_POLITICAL_LEANING',
    'get_source_credibility',
    'get_source_political_leaning',
    'fetch_article_text',
    'fetch_similar_articles',
    'generate_insight'
]
