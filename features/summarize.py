"""
Summarize News Feature
Summarizes pasted news articles
"""
import streamlit as st
from utils.models import summarize_text


def run_summarize_feature():
    """Main function for Summarize News feature"""
    
    st.subheader("Summarize Article")
    news = st.text_area("Paste the news article to summarize:", height=200)
    
    if st.button("📝 Summarize", use_container_width=True):
        if news.strip():
            with st.spinner("Summarizing..."):
                summary = summarize_text(news)
                st.success("**Summary:**")
                st.write(summary)
        else:
            st.warning("Please enter some news text to summarize.")
