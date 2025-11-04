
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
    
    # Create tabs for single vs batch analysis
    tab1, tab2 = st.tabs(["🔍 Single Source", "📊 Batch Analysis"])
    
    with tab1:
        st.markdown("#### 🔗 Enter Source Information")
        
        # Auto-complete suggestions based on common domains
        common_sources = [
            "cnn.com", "bbc.com", "reuters.com", "ap.org", "nytimes.com",
            "wsj.com", "guardian.com", "foxnews.com", "npr.org", "usatoday.com"
        ]
        
        url_input = st.text_input(
            "News URL or Domain",
            placeholder="e.g., https://example.com/article or example.com",
            help="Enter a complete URL or just the domain name. Try: " + ", ".join(common_sources[:3])
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
                st.caption(f"🌐 Ready to analyze: **{domain}**")
        
        if st.button("🔍 Analyze Source", use_container_width=True, type="primary"):
            _analyze_single_source(url_input, _normalize_url)
    
    with tab2:
        st.markdown("#### 📊 Analyze Multiple Sources")
        st.caption("Enter multiple URLs or domains, one per line")
        
        batch_input = st.text_area(
            "Multiple Sources",
            height=150,
            placeholder="cnn.com\nbbc.com\nfoxnews.com\n...",
            help="Enter one URL or domain per line"
        )
        
        if st.button("🔍 Analyze All Sources", use_container_width=True, type="primary"):
            if batch_input.strip():
                sources = [line.strip() for line in batch_input.split('\n') if line.strip()]
                if sources:
                    _analyze_batch_sources(sources)
                else:
                    st.warning("Please enter at least one source")
            else:
                st.warning("Please enter sources to analyze")


def _analyze_single_source(url_input, normalize_func):
    """Analyze a single source with enhanced feedback"""
    if not url_input.strip():
        st.warning("⚠️ Please enter a URL or domain to analyze.")
        return
        
    url = normalize_func(url_input)
    if not url:
        return
        
    # Use cached analysis for better performance
    with st.spinner("Analyzing source..."):
        cred_label, cred_desc, lean_label, error = _cached_source_analysis(url)
    
    if error:
        st.error(f"❌ Could not analyze source: {error}")
        return
        
    # Show results
    _display_analysis_results(cred_label, cred_desc, lean_label)


def _analyze_batch_sources(sources):
    """Analyze multiple sources efficiently"""
    st.markdown("### 📊 Batch Analysis Results")
    
    progress_bar = st.progress(0)
    results = []
    
    for i, source in enumerate(sources):
        progress_bar.progress((i + 1) / len(sources))
        
        # Normalize source
        if not source.startswith('http'):
            source = f"https://{source}"
            
        try:
            cred_label, cred_desc, lean_label, error = _cached_source_analysis(source)
            domain = _extract_domain_fast(source)
            
            results.append({
                'domain': domain,
                'credibility': cred_label or 'Unknown',
                'leaning': lean_label or 'Unknown',
                'error': error
            })
        except Exception as e:
            results.append({
                'domain': _extract_domain_fast(source),
                'credibility': 'Error',
                'leaning': 'Error',
                'error': str(e)
            })
    
    progress_bar.empty()
    
    # Display batch results in a table
    if results:
        st.markdown("#### Summary Table")
        import pandas as pd
        
        df = pd.DataFrame(results)
        df = df[df['error'].isna() | (df['error'] == '')]  # Filter out errors for main table
        
        if not df.empty:
            # Color code the credibility column
            def color_credibility(val):
                if val == 'High Credibility':
                    return 'background-color: #d4edda'
                elif val == 'Mixed Credibility':
                    return 'background-color: #fff3cd'
                elif val in ['Questionable', 'Low Credibility']:
                    return 'background-color: #f8d7da'
                return ''
            
            styled_df = df.style.applymap(color_credibility, subset=['credibility'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Quick statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                high_cred = len(df[df['credibility'] == 'High Credibility'])
                st.metric("High Credibility", high_cred)
            with col2:
                mixed_cred = len(df[df['credibility'] == 'Mixed Credibility'])
                st.metric("Mixed Credibility", mixed_cred)
            with col3:
                low_cred = len(df[df['credibility'].isin(['Questionable', 'Low Credibility'])])
                st.metric("Low/Questionable", low_cred)


def _display_analysis_results(cred_label, cred_desc, lean_label):
    """Display analysis results with enhanced visuals"""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Analysis Results")

    # Display results in clean metrics
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("#### 🏆 Credibility")
        if cred_label == "High Credibility":
            st.success(f"**{cred_label}**")
            st.markdown("✅ Trusted Source")
        elif cred_label == "Mixed Credibility":
            st.warning(f"**{cred_label}**")
            st.markdown("⚠️ Use with Caution")
        elif cred_label in ("Questionable", "Satire", "Low Credibility"):
            st.error(f"**{cred_label}**")
            st.markdown("❌ Unreliable Source")
        else:
            st.info(f"**{cred_label}**")
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
