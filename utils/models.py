"""
Machine Learning models and pipeline loaders for News Analyzer Platform
"""
import streamlit as st
from transformers import pipeline
import joblib


# ========== PIPELINE LOADERS ==========
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")


@st.cache_resource
def load_sentiment_analyzer():
    return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")


@st.cache_resource
def load_insight_model():
    """Load text generation model with fallback options"""
    try:
        return pipeline("text2text-generation", model="google/flan-t5-large")
    except Exception:
        try:
            # Fallback to smaller model
            return pipeline("text2text-generation", model="google/flan-t5-base")
        except Exception:
            try:
                # Final fallback to summarization model
                return pipeline("summarization", model="facebook/bart-large-cnn")
            except Exception:
                return None


@st.cache_resource
def load_ner():
    return pipeline(
        "ner",
        grouped_entities=True,
        model="dbmdz/bert-large-cased-finetuned-conll03-english"
    )


@st.cache_resource
def load_whisper():
    return pipeline("automatic-speech-recognition", model="openai/whisper-base")


@st.cache_resource
def load_zeroshot():
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


# ========== MODEL FUNCTIONS ==========
def load_fake_news_model():
    """Load the trained fake news detection model and vectorizer"""
    vectorizer = joblib.load('data/vectorizer.joblib')
    model = joblib.load('data/model.joblib')
    return vectorizer, model


def summarize_text(text):
    """Summarize text with error handling"""
    try:
        summarizer = load_summarizer()
        if not summarizer:
            return text[:200] + "..." if len(text) > 200 else text
        
        # Clean and limit text
        text = text.strip()
        if len(text) < 50:
            return text
        
        # Limit input length to avoid memory issues
        max_input_length = 1000
        if len(text) > max_input_length:
            text = text[:max_input_length]
        
        summary = summarizer(text, max_length=100, min_length=20, do_sample=False)
        if summary and len(summary) > 0:
            return summary[0]['summary_text']
        return text[:200] + "..." if len(text) > 200 else text
        
    except Exception as e:
        print(f"Summarization failed: {e}")
        # Return truncated text as fallback
        return text[:200] + "..." if len(text) > 200 else text


def analyze_sentiment(text):
    """Analyze sentiment with error handling"""
    try:
        sentiment_analyzer = load_sentiment_analyzer()
        if not sentiment_analyzer:
            return "Unknown"
        
        # Limit text length to avoid errors
        text = text[:1000] if len(text) > 1000 else text
        
        result = sentiment_analyzer(text)
        if result and len(result) > 0:
            label = result[0].get('label', 'Unknown')
            # Convert label to more readable format
            if 'POSITIVE' in label.upper():
                return 'Positive'
            elif 'NEGATIVE' in label.upper():
                return 'Negative'
            else:
                return 'Neutral'
        return "Unknown"
    except Exception as e:
        print(f"Sentiment analysis failed: {e}")
        return "Unknown"


def extract_entities(text):
    """Extract named entities with error handling"""
    try:
        ner = load_ner()
        if not ner:
            return {}
        
        # Limit text length to avoid errors
        text = text[:2000] if len(text) > 2000 else text
        
        entities = ner(text)
        if not entities:
            return {}
        
        results = {}
        for ent in entities:
            try:
                label = ent.get('entity_group', 'OTHER')
                word = ent.get('word', '').replace(" ##", "").strip()
                if word and len(word) > 1:  # Filter out single characters
                    results.setdefault(label, set()).add(word)
            except Exception:
                continue
        
        # Convert sets to sorted lists and filter empty categories
        return {label: sorted(list(words)) for label, words in results.items() if words}
        
    except Exception as e:
        print(f"Entity extraction failed: {e}")
        return {}


def classify_political_leaning_text(text: str):
    clf = load_zeroshot()
    labels = ["left-leaning", "center", "right-leaning"]
    res = clf(
        text,
        candidate_labels=labels,
        hypothesis_template="This article has a {} political bias.",
        multi_label=False
    )
    top = res["labels"][0]
    scores = dict(zip(res["labels"], [float(s) for s in res["scores"]]))
    return top, scores


def predict_proba_content_only(text: str, stop_words, preprocess_func) -> float:
    """Content-only probability of being REAL (0..1) using TF-IDF model + zero-shot ensemble."""
    vectorizer, model = load_fake_news_model()
    processed = preprocess_func(text, stop_words)
    base_proba = float(model.predict_proba(vectorizer.transform([processed]))[0][1])
    
    try:
        zs = load_zeroshot()
        res = zs(
            text[:1200],
            candidate_labels=["real news", "fake news"],
            hypothesis_template="This is {}.",
            multi_label=False,
        )
        if "real news" in res["labels"]:
            pz = float(res["scores"][res["labels"].index("real news")])
        else:
            pz = 0.5
    except Exception:
        pz = 0.5
    
    p = 0.6 * base_proba + 0.4 * pz
    return float(min(0.995, max(0.005, p)))
