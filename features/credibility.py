
"""
Source Credibility Analyzer Feature
Evaluates credibility and political leaning of news sources
"""
import streamlit as st
import re
from functools import lru_cache
from urllib.parse import urlparse
from utils.source_data import get_source_credibility, get_source_political_leaning


# Cache results for recently analyzed sources (improves performance)
@lru_cache(maxsize=128)
def _cached_source_analysis(normalized_url: str):
    """Cache analysis results to avoid repeated API/database calls"""
    try:
        cred_label, cred_desc = get_source_credibility(normalized_url)
        lean_label = get_source_political_leaning(normalized_url)
        return cred_label, cred_desc, lean_label, None
    except Exception as e:
        return None, None, None, str(e)


def _extract_domain_fast(url: str) -> str:
    """Fast domain extraction for validation"""
    try:
        if not re.match(r"^https?://", url):
            url = "https://" + url
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix for consistency
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""


def _validate_url_format(url: str) -> tuple[bool, str]:
    """Quick validation before processing"""
    if not url or len(url.strip()) < 3:
        return False, "URL too short"
    
    # Check for basic URL patterns
    url = url.strip().lower()
    if not any(pattern in url for pattern in ['.com', '.org', '.net', '.edu', '.gov', '.co.', '.news']):
        return False, "Invalid domain format"
    
    # Check for suspicious patterns
    if any(char in url for char in ['<', '>', '"', "'"]):
        return False, "Invalid characters in URL"
    
    return True, ""


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
        """Enhanced URL normalization with validation"""
        s = (s or "").strip()
        if not s:
            return ""
        
        # Quick validation first
        is_valid, error_msg = _validate_url_format(s)
        if not is_valid:
            st.error(f"⚠️ {error_msg}")
            return ""
        
        # Normalize URL format
        if not re.match(r"^https?://", s):
            s = "https://" + s
        return s

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Add quick domain preview for user feedback
    if url_input.strip():
        domain = _extract_domain_fast(url_input)
        if domain:
            st.caption(f"🌐 Analyzing domain: **{domain}**")
    
    if st.button("🔍 Analyze Source", use_container_width=True, type="primary"):
        if not url_input.strip():
            st.warning("⚠️ Please enter a URL or domain to analyze.")
        else:
            url = _normalize_url(url_input)
            if url:  # Only proceed if normalization succeeded
                # Use cached analysis for better performance
                cred_label, cred_desc, lean_label, error = _cached_source_analysis(url)
                
                if error:
                    st.error(f"❌ Could not analyze source: {error}")
                else:
                    # Show results immediately (no artificial spinner delay)
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

# Clear cache when needed (optional - for development/testing)
def clear_credibility_cache():
    """Clear the analysis cache to force fresh lookups"""
    _cached_source_analysis.cache_clear()
