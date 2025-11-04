"""
News Verification Tool
Text analysis for news article authenticity assessment
"""
import streamlit as st
import time
import re
from utils.helpers import is_opinion_piece
from utils.models import classify_political_leaning_text, load_zeroshot
from utils.source_data import get_source_political_leaning


def _predict_proba_ensemble(text: str, url_hint: str | None, model, vectorizer, preprocess_func, stop_words) -> float:
    """
    Enhanced ensemble prediction with multiple verification layers
    Returns probability of being REAL (0.0 to 1.0)
    """
    if not text or len(text.strip()) < 10:
        return 0.5  # Neutral for insufficient content
    
    # 1. Base TF-IDF model prediction
    try:
        processed = preprocess_func(text, stop_words)
        base_proba = float(model.predict_proba(vectorizer.transform([processed]))[0][1])
    except Exception:
        base_proba = 0.5

    # 2. Zero-shot classification with better prompting
    zs_proba = 0.5
    try:
        zs = load_zeroshot()
        # Use more specific labels and better hypothesis
        res = zs(
            text[:1000],
            candidate_labels=["legitimate news article", "misleading or fake content"],
            hypothesis_template="This text is {}.",
            multi_label=False
        )
        if "legitimate news article" in res["labels"]:
            zs_proba = float(res["scores"][res["labels"].index("legitimate news article")])
    except Exception:
        pass

    # 3. Content quality indicators
    quality_score = _assess_content_quality(text)
    
    # 4. Enhanced ensemble with content quality weighting
    # Give more weight to quality indicators when models disagree
    model_agreement = abs(base_proba - zs_proba)
    
    if model_agreement < 0.2:  # Models agree
        ensemble_proba = 0.7 * base_proba + 0.3 * zs_proba
    else:  # Models disagree - use quality score as tiebreaker
        ensemble_proba = 0.4 * base_proba + 0.3 * zs_proba + 0.3 * quality_score
    
    # 5. Apply quality adjustment
    final_proba = (ensemble_proba + quality_score) / 2
    
    return float(min(0.99, max(0.01, final_proba)))


def _assess_content_quality(text: str) -> float:
    """
    Assess content quality indicators that correlate with authenticity
    Returns score between 0.0 (low quality) and 1.0 (high quality)
    """
    import re
    
    quality_indicators = []
    text_lower = text.lower()
    
    # Length and structure indicators
    word_count = len(text.split())
    sentence_count = len(re.findall(r'[.!?]+', text))
    
    # 1. Appropriate length (not too short, not suspiciously long)
    if 50 <= word_count <= 2000:
        quality_indicators.append(0.8)
    elif 20 <= word_count < 50 or 2000 < word_count <= 3000:
        quality_indicators.append(0.6)
    else:
        quality_indicators.append(0.3)
    
    # 2. Proper sentence structure
    if sentence_count > 0:
        avg_sentence_length = word_count / sentence_count
        if 10 <= avg_sentence_length <= 30:
            quality_indicators.append(0.8)
        else:
            quality_indicators.append(0.5)
    
    # 3. Attribution and sources
    source_indicators = ['according to', 'sources say', 'reported by', 'study shows', 
                        'research indicates', 'officials said', 'spokesperson']
    if any(indicator in text_lower for indicator in source_indicators):
        quality_indicators.append(0.9)
    else:
        quality_indicators.append(0.4)
    
    # 4. Direct quotes (generally more credible)
    if '"' in text or "'" in text:
        quality_indicators.append(0.8)
    else:
        quality_indicators.append(0.5)
    
    # 5. Specific details (dates, numbers, names)
    has_dates = bool(re.search(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', text))
    has_numbers = bool(re.search(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text))
    has_proper_nouns = len(re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)) > 2
    
    if has_dates and has_numbers and has_proper_nouns:
        quality_indicators.append(0.9)
    elif (has_dates and has_numbers) or (has_dates and has_proper_nouns):
        quality_indicators.append(0.7)
    elif has_dates or has_numbers or has_proper_nouns:
        quality_indicators.append(0.6)
    else:
        quality_indicators.append(0.3)
    
    # 6. Red flags for fake news
    red_flags = ['shocking truth', 'doctors hate', 'secret revealed', 'they don\'t want you',
                'mainstream media won\'t', 'wake up', 'sheeple', 'big pharma conspiracy']
    if any(flag in text_lower for flag in red_flags):
        quality_indicators.append(0.1)  # Strong negative indicator
    else:
        quality_indicators.append(0.7)
    
    # 7. Emotional manipulation indicators
    emotional_words = ['unbelievable', 'shocking', 'amazing', 'incredible', 'outrageous',
                      'devastating', 'terrifying', 'miraculous']
    emotional_count = sum(1 for word in emotional_words if word in text_lower)
    if emotional_count == 0:
        quality_indicators.append(0.8)
    elif emotional_count <= 2:
        quality_indicators.append(0.6)
    else:
        quality_indicators.append(0.2)
    
    # Return weighted average
    return sum(quality_indicators) / len(quality_indicators)


def run_paste_news_feature(model, vectorizer, stop_words, preprocess_func, fetch_article_text):
    """Main function for Paste/Type News feature"""
    
    # Main header
    st.subheader("News Article Verification")
    st.write("Check the credibility and authenticity of news content")
    # Local helper (scoped to this feature)
    def _get_article_text_or_content(value: str) -> str:
        value = (value or "").strip()
        if not value:
            return ""
        if re.match(r'https?://', value):
            text = fetch_article_text(value) or ""
            # Trim boilerplate: keep the most informative start
            words = text.split()
            return " ".join(words[:600])
        return value

    with st.container():
        # Input section using a form for better UX
        st.markdown("### Content Input")
        with st.form(key="verify_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                title = st.text_input(
                    "Article Title (Optional)",
                    placeholder="Enter the headline...",
                    help="Adding the title can improve analysis accuracy"
                )
                user_input = st.text_area(
                    "Article Text or URL",
                    height=320,
                    placeholder="Paste the full article text here, or enter a news URL to analyze...",
                    help="You can paste article content directly or provide a URL for analysis"
                )
                st.caption("Tip: Paste article text or enter a news URL. Title is optional.")
            with col2:
                # Reserved for small controls or future metadata (kept empty intentionally)
                st.write("")

            submitted = st.form_submit_button("🔍 Analyze")

    # Small spacer to separate form from results/messages
    st.markdown("<br>", unsafe_allow_html=True)

    # Handle form submission
    if 'submitted' in locals() and submitted:
        # Build content from title + article text (if URL, fetch content)
        title_text = (title or "").strip()
        user_val = (user_input or "").strip()
        if not user_val and not title_text:
            st.warning("Please enter some news text or URL to analyze.")
        else:
            content_text = _get_article_text_or_content(user_val) if user_val else ""
            combined_text = ". ".join([t for t in [title_text, content_text] if t]).strip()

            # Auto-detect source URL from user input if it's a URL (for internal processing only)
            effective_source_url = user_val if re.match(r'^https?://', user_val) else ""

            if combined_text.strip():
                with st.spinner("🔄 Analyzing news article..."):
                    time.sleep(0.3)  # Brief pause for UX
                    
                # Results container
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📊 Analysis Results")
                
                # Opinion handling: show not-rated verdict and skip classifier
                if is_opinion_piece(combined_text, effective_source_url):
                    st.info("**Opinion/Editorial Content** - This appears to be opinion-based content rather than factual reporting.")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Content Type", "Opinion")
                    with col2:
                        st.metric("Assessment", "Not Applicable")
                    with col3:
                        st.metric("Confidence", "N/A")
                else:
                    # Enhanced prediction with better confidence calculation
                    proba = _predict_proba_ensemble(combined_text, effective_source_url, model, vectorizer, preprocess_func, stop_words)

                    # Improved verdict logic with confidence thresholds
                    if proba >= 0.7:
                        verdict = "Likely Real"
                        verdict_confidence = "High"
                        color = "success"
                    elif proba >= 0.55:
                        verdict = "Possibly Real"
                        verdict_confidence = "Medium"
                        color = "info"
                    elif proba >= 0.45:
                        verdict = "Uncertain"
                        verdict_confidence = "Low"
                        color = "warning"
                    elif proba >= 0.3:
                        verdict = "Possibly Fake"
                        verdict_confidence = "Medium"
                        color = "warning"
                    else:
                        verdict = "Likely Fake"
                        verdict_confidence = "High"
                        color = "error"
                    
                    # Calculate display confidence (0-100%)
                    if proba > 0.5:
                        display_confidence = proba
                    else:
                        display_confidence = 1 - proba
                    
                    confidence_percentage = int(display_confidence * 100)
                    
                    # Display verdict with improved messaging
                    if color == "success":
                        st.success(f"**Assessment: {verdict}** - Content appears credible and well-sourced")
                    elif color == "info":
                        st.info(f"**Assessment: {verdict}** - Content shows signs of credibility but verify key claims")
                    elif color == "warning":
                        st.warning(f"**Assessment: {verdict}** - Content reliability is unclear, cross-check with other sources")
                    else:
                        st.error(f"**Assessment: {verdict}** - Content shows multiple reliability issues")
                    
                    # Enhanced results display
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Classification", verdict)
                    with col2:
                        st.metric("Confidence", f"{confidence_percentage}%")
                    with col3:
                        st.metric("Certainty", verdict_confidence)
                    
                    # Add explanation of the assessment
                    with st.expander("ℹ️ Understanding Your Results"):
                        st.markdown(f"""
                        **Classification Explanation:**
                        - **Raw Score**: {proba:.3f} (closer to 1.0 = more likely real, closer to 0.0 = more likely fake)
                        - **Assessment Logic**: 
                          - 0.7+ = Likely Real (strong positive indicators)
                          - 0.55-0.69 = Possibly Real (some positive indicators)
                          - 0.45-0.54 = Uncertain (mixed signals)
                          - 0.3-0.44 = Possibly Fake (some red flags)
                          - <0.3 = Likely Fake (multiple red flags)
                        
                        **Factors Analyzed:**
                        - Content structure and writing quality
                        - Presence of sources and attribution
                        - Emotional vs factual language
                        - Specific details (dates, names, numbers)
                        - Common misinformation patterns
                        
                        **Recommendation**: Always cross-check important claims with multiple reliable sources.
                        """)

    st.markdown("---")
