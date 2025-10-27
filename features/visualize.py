"""
Visualize Keywords Feature
Shows word frequency distribution in news articles
"""
import streamlit as st
import matplotlib.pyplot as plt
import re
from collections import Counter


def show_word_frequency_pie_chart(text, num_words, stop_words):
    """Generate and display word frequency pie chart"""
    words = re.findall(r'\b\w+\b', text.lower())
    words = [w for w in words if w not in stop_words]
    most_common = Counter(words).most_common(num_words)
    
    if not most_common:
        st.info("Not enough words to visualize.")
        return
    
    labels, values = zip(*most_common)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    ax.set_title("Most Frequent Words in Article")
    st.pyplot(fig)


def run_visualize_feature(stop_words):
    """Main function for Visualize Keywords feature"""
    
    st.subheader("🥧 News Word Frequency Distribution")
    news = st.text_area("Paste the news article to visualize word frequency:", height=200)
    
    if st.button("Show Word Frequency Pie Chart", use_container_width=True):
        if news.strip():
            with st.spinner("Generating word frequency pie chart..."):
                show_word_frequency_pie_chart(news, num_words=10, stop_words=stop_words)
        else:
            st.warning("Please enter some news text to visualize.")
