"""
Source Credibility Analyzer Feature
Evaluates credibility and political leaning of news sources
"""
import streamlit as st
import re
from utils.source_data import get_source_credibility, get_source_political_leaning


def run_credibility_feature():
    """Main function for Source Credibility Analyzer feature"""
    
    # Feature header
    st.markdown("""
    <div class='feature-description'>
        <h2 style='margin:0 0 0.5rem 0; color:white;'>🎯 Source Credibility Analyzer</h2>
        <p style='margin:0; font-size:1.05em; opacity:0.95;'>
            Evaluate the credibility and political leaning of news sources instantly
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 🔗 Enter Source Information")
    url_input = st.text_input(
        "News URL or Domain",
        placeholder="e.g., https://example.com/article or example.com",
        help="Enter a complete URL or just the domain name"
    )

    def _normalize_url(s: str) -> str:
        s = (s or "").strip()
        if not s:
            return ""
        # allow plain domains like example.com
        if not re.match(r"^https?://", s):
            s = "https://" + s
        return s

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔍 Analyze Source", use_container_width=True, type="primary"):
        if not url_input.strip():
            st.warning("⚠️ Please enter a URL or domain to analyze.")
        else:
            url = _normalize_url(url_input)
            try:
                with st.spinner("🔄 Analyzing source credibility..."):
                    cred_label, cred_desc = get_source_credibility(url)
                    lean_label = get_source_political_leaning(url)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📊 Analysis Results")

                # Display results in clean metrics
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.markdown("#### 🏆 Credibility")
                    if cred_label == "High Credibility":
                        st.success(f"**{cred_label}**")  # Green
                        st.markdown("✅ Trusted Source")
                    elif cred_label == "Mixed Credibility":
                        st.warning(f"**{cred_label}**")  # Orange
                        st.markdown("⚠️ Use with Caution")
                    elif cred_label in ("Questionable", "Satire", "Low Credibility"):
                        st.error(f"**{cred_label}**")  # Red
                        st.markdown("❌ Unreliable Source")
                    else:
                        st.info(f"**{cred_label}**")  # Blue for Unknown
                        st.markdown("❓ Unknown Source")
                
                with col2:
                    st.markdown("#### ⚖️ Political Leaning")
                    leaning_display = lean_label.capitalize() if lean_label != 'unknown' else 'Unknown'
                    if lean_label == 'left-leaning':
                        st.info(f"**{leaning_display}**")
                    elif lean_label == 'right-leaning':
                        st.info(f"**{leaning_display}**")
                    elif lean_label == 'center':
                        st.success(f"**{leaning_display}**")
                    else:
                        st.info(f"**{leaning_display}**")
                    st.markdown("📊 Editorial Stance")
                
                with col3:
                    st.markdown("#### 📈 Recommendation")
                    if cred_label == "High Credibility":
                        st.success("**Recommended**")
                        st.markdown("👍 Safe to Use")
                    elif cred_label == "Mixed Credibility":
                        st.warning("**Verify Facts**")
                        st.markdown("🔍 Cross-check Info")
                    else:
                        st.error("**Not Recommended**")
                        st.markdown("⛔ Avoid Source")

                # Show description if available
                if cred_desc:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("📖 About this source", expanded=True):
                        st.markdown(f"**Source Information:**\n\n{cred_desc}")

                # Info for unknown sources
                st.markdown("<br>", unsafe_allow_html=True)
                if cred_label == "Unknown":
                    st.info("💡 **Note:** This source is not in our database yet. Exercise caution and cross-reference with multiple reputable sources.")
                else:
                    st.caption("ℹ️ Source assessment based on established credibility databases and journalistic standards.")
                    
            except Exception as e:
                st.error(f"❌ Could not analyze source: {e}")
