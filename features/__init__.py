"""
Features package for News Analyzer Platform
Each feature module contains the UI and logic for a specific feature
"""
from .paste_news import run_paste_news_feature
from .fetch_news import run_fetch_news_feature
from .summarize import run_summarize_feature
from .summarize_link import run_summarize_link_feature
from .fact_check import run_fact_check_feature
from .video_news import run_video_news_feature
from .ai_insight import run_ai_insight_feature
from .visualize import run_visualize_feature
from .translate import run_translate_feature
from .timeline import run_timeline_feature
from .credibility import run_credibility_feature

__all__ = [
    'run_paste_news_feature',
    'run_fetch_news_feature',
    'run_summarize_feature',
    'run_summarize_link_feature',
    'run_fact_check_feature',
    'run_video_news_feature',
    'run_ai_insight_feature',
    'run_visualize_feature',
    'run_translate_feature',
    'run_timeline_feature',
    'run_credibility_feature'
]
