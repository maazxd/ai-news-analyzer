"""
Utility functions and helper methods for News Analyzer Platform
"""
import streamlit as st
import re
import requests
import pandas as pd
from nltk.stem.porter import PorterStemmer
from langdetect import detect, LangDetectException
import os

ps = PorterStemmer()


# ========== SECRETS/ENV HELPERS ==========
def get_secret_or_env(key: str, default: str = "") -> str:
    """
    Safely get a secret: prefer Streamlit secrets, then environment, else default.
    Avoids StreamlitSecretNotFoundError when no secrets.toml exists.
    """
    try:
        val = st.secrets[key]
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key, default)


# ========== TEXT PREPROCESSING ==========
def preprocess(text, stop_words):
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = text.split()
    text = [ps.stem(word) for word in text if word not in stop_words]
    return ' '.join(text)


def is_valid_news(text):
    if len(text.split()) < 5:
        return False
    code_indicators = ['{', '}', ';', '()', 'def', 'import', 'print']
    if any(indicator in text for indicator in code_indicators):
        return False
    return True


def is_opinion_piece(text: str, url: str = "") -> bool:
    """
    Heuristic detector for opinion/analysis content.
    Returns True if URL or text strongly suggests an opinion column.
    """
    text_l = (text or "").lower()
    url_l = (url or "").lower()
    markers = [
        "opinion", "op-ed", "oped", "editorial", "analysis",
        "commentary", "columns"
    ]
    if any(f"/{m}/" in url_l for m in markers):
        return True
    subjective = [
        "i think", "i believe", "in my view", "we should", "i feel",
        "my opinion", "i argue", "i suggest", "in our view", "personally",
        "from my perspective"
    ]
    subjective_hits = sum(1 for s in subjective if s in text_l)
    first_40 = " ".join(text_l.split()[:40])
    pattern = r"\\b(" + "|".join(re.escape(m) for m in markers) + r")\\b"
    if re.search(pattern, first_40):
        return True
    return subjective_hits >= 2


# ========== BIAS DETECTION ==========
BIAS_LEXICON = [
    "shocking", "outrage", "scandal", "cover-up", "exposed", "plot", "agenda", "propaganda",
    "rigged", "fake", "hoax", "catastrophe", "disaster", "crisis", "meltdown", "massive",
    "unprecedented", "slam", "blast", "brutal", "controversial", "alarming", "warning"
]


def detect_bias_signals(text: str):
    words = re.findall(r"\\b\\w+\\b", text.lower())
    hits = [w for w in words if w in BIAS_LEXICON]
    if not words:
        return 0, {}
    score = min(100, int((len(hits) / max(1, len(words))) * 3000))
    counts = dict(pd.Series(hits).value_counts()) if hits else {}
    return score, counts


# ========== LANGUAGE DETECTION ==========
def detect_language(text):
    try:
        lang = detect(text)
        lang_map = {
            'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
            'it': 'Italian', 'ru': 'Russian', 'ar': 'Arabic', 'zh-cn': 'Chinese', 'hi': 'Hindi'
        }
        return lang, lang_map.get(lang, lang)
    except LangDetectException:
        return "", "Could not detect language"


# ========== SOCIAL MEDIA TEXT CLEANING ==========
def clean_social_text(text: str) -> str:
    """Remove URLs, mentions, trailing signatures, emojis, and normalize whitespace."""
    t = (text or "")
    t = re.sub(r"https?://\\S+", " ", t)
    t = re.sub(r"pic\\.twitter\\.com/\\S+", " ", t)
    t = re.sub(r"\\bRT\\b", " ", t)
    t = re.sub(r"@[A-Za-z0-9_]+", " ", t)
    t = re.sub(r"#(\\w+)", r"\\1", t)
    t = re.sub(r"—\\s[^\\n]+\\(@[^\\)]+\\)\\s+[A-Za-z]+\\s+\\d{1,2},\\s+\\d{4}", " ", t)
    try:
        t = re.sub(r"[\\U0001F300-\\U0001FAFF\\U00002700-\\U000027BF]", " ", t)
    except re.error:
        pass
    t = re.sub(r"\\s+", " ", t).strip()
    return t


# ========== FACT-CHECK HELPERS ==========
def fact_check_claims(text, api_key, max_claims=3):
    sentences = re.split(r'(?<=[.!?]) +', text)
    claims = sentences[:max_claims]
    results = []
    for claim in claims:
        url = (
            "https://factchecktools.googleapis.com/v1alpha1/claims:search"
            f"?query={requests.utils.quote(claim)}&key={api_key}"
        )
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if "claims" in data and data["claims"]:
                for c in data["claims"]:
                    result = {
                        "text": claim,
                        "claim": c.get("text", ""),
                        "claimant": c.get("claimant", ""),
                        "claimReview": c.get("claimReview", [{}])[0].get("textualRating", ""),
                        "url": c.get("claimReview", [{}])[0].get("url", "")
                    }
                    results.append(result)
            else:
                results.append({"text": claim, "claim": None})
        else:
            results.append({"text": claim, "claim": None})
    return results


def normalize_factcheck_rating(rating: str) -> str:
    """Map varied textual ratings to one of: 'supports', 'refutes', 'mixed'."""
    r = (rating or "").strip().lower()
    if not r:
        return "mixed"
    positive = [
        "true", "mostly true", "correct", "accurate", "verified", "supported", "fact", "legit"
    ]
    negative = [
        "false", "mostly false", "pants on fire", "incorrect", "misleading", "fabricated",
        "no evidence", "debunked", "hoax"
    ]
    neutral = [
        "partly true", "half true", "mixed", "needs context", "unproven", "unclear",
        "insufficient", "context"
    ]
    if any(k in r for k in positive):
        return "supports"
    if any(k in r for k in negative):
        return "refutes"
    if any(k in r for k in neutral):
        return "mixed"
    return "mixed"
