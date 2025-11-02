"""
Summarize from Link Feature
Fetches and summarizes news from URLs
"""
import streamlit as st
from utils.helpers import detect_language
from utils.models import load_summarizer


def run_summarize_link_feature(fetch_article_text):
    """Main function for Summarize from Link feature"""
    
    st.subheader("🔗 Summarize News from Article Link")
    url = st.text_input("Paste the news article URL here:")
    summary_length_words = st.slider("Summary length (approx. words)", min_value=30, max_value=200, value=50, step=10)
    summary_length = summary_length_words * 2  # Convert to tokens (approximate)
    st.caption("Note: Summary length is approximate. Actual output may vary.")
    
    if st.button("Get Summary", use_container_width=True):
        if url.strip():
            with st.spinner("Fetching and summarizing article..."):
                text = fetch_article_text(url)
                if text and len(text.split()) > 20:
                    detected_lang, detected_lang_name = detect_language(text)
                    st.info(f"**Detected Language:** {detected_lang_name} ({detected_lang})")
                    try:
                        summary = load_summarizer()(
                            text,
                            max_length=summary_length,
                            min_length=int(summary_length * 0.5),
                            do_sample=False
                        )[0]['summary_text']
                        st.success("**Summary:**")
                        st.write(summary)
                    except Exception as e:
                        st.error(f"Summarization failed: {e}")
                else:
                    st.error("Could not extract article content from this URL. This might be due to:")
                    st.markdown("""
                    - **Website blocking**: Some sites block automated access
                    - **Paywall or login required**: Content might be behind a paywall
                    - **JavaScript-heavy site**: Content might load dynamically
                    - **Network issues**: Connection problems
                    
                    **Try:**
                    - A different news article URL
                    - Copy-paste the article text directly using the 'Article Summary' feature
                    - Using articles from major news sites (BBC, Reuters, etc.)
                    """)
        else:
            st.warning("Please enter a news article URL.")
