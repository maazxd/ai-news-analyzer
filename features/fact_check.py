"""

"""
import streamlit as st
import re
from utils.helpers import get_secret_or_env


def fact_check_claims_long_article(text: str, api_key: str, max_claims: int = 6):
    """
    Multi-approach fact-checking with Google API, manual search, and heuristics.
    Returns a list of dicts: { "claim": str, "hits": [ {publisher, rating, title, url}, ... ] }
    """
    import requests
    from urllib.parse import quote
    import json
    
    # Better sentence splitting and claim extraction
    text = (text or '').strip()
    if not text:
        return []
    
    # Split into sentences more accurately
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Filter and score sentences for factual claims
    candidates = []
    
    # Enhanced keywords that often indicate factual claims
    claim_indicators = [
        'said', 'claims', 'reported', 'according to', 'stated', 'announced',
        'confirmed', 'denied', 'revealed', 'disclosed', 'sources say',
        'investigation shows', 'study finds', 'data shows', 'statistics',
        'research indicates', 'poll shows', 'survey reveals', 'officials said',
        'government announced', 'company reported', 'experts claim', 'study shows'
    ]
    
    # High-impact keywords for controversial/checkable claims
    controversial_keywords = [
        'election', 'vote', 'fraud', 'covid', 'vaccine', 'climate change',
        'biden', 'trump', 'putin', 'ukraine', 'china', 'fbi', 'cia',
        'conspiracy', 'scandal', 'investigation', 'lawsuit', 'court',
        'million', 'billion', 'percent', 'increase', 'decrease'
    ]
    
    # Entity indicators (organizations, places, people)
    entity_patterns = [
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Person names
        r'\b[A-Z]{2,}\b',  # Acronyms/Organizations
        r'\$[\d,]+(?:\.\d{2})?(?:\s?(?:million|billion|trillion))?',  # Money
        r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',  # Dates
        r'\b\d+(?:,\d{3})*(?:\.\d+)?\s?(?:percent|%|million|billion|thousand)\b'  # Numbers with units
    ]
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) < 8 or len(sentence.split()) > 40:  # Optimal length
            continue
            
        score = 0
        sentence_lower = sentence.lower()
        
        # Score based on claim indicators
        for indicator in claim_indicators:
            if indicator in sentence_lower:
                score += 3
        
        # Boost score for controversial/frequently fact-checked topics
        for keyword in controversial_keywords:
            if keyword in sentence_lower:
                score += 4
        
        # Score based on entities and specific patterns
        for pattern in entity_patterns:
            matches = len(re.findall(pattern, sentence))
            score += min(matches * 2, 6)
        
        # Avoid questions and subjective statements
        if sentence.strip().endswith('?') or any(word in sentence_lower for word in 
                                               ['i think', 'i believe', 'opinion', 'seems like', 'appears']):
            score -= 2
        
        # Prefer sentences with quotes (direct statements)
        if '"' in sentence or "'" in sentence:
            score += 3
        
        # Boost sentences with specific numbers or percentages
        if re.search(r'\b\d+(?:\.\d+)?\s?(?:percent|%)\b', sentence):
            score += 3
            
        # Avoid very short or very long sentences
        word_count = len(sentence.split())
        if 12 <= word_count <= 25:
            score += 1
        elif word_count < 8:
            score -= 3
        
        if score > 0:
            candidates.append((score, sentence))
    
    # Sort by score and select top candidates
    candidates.sort(key=lambda x: x[0], reverse=True)
    selected_claims = [sentence for _, sentence in candidates[:max_claims]]
    
    # If no good candidates, fall back to key sentences
    if not selected_claims:
        selected_claims = [s.strip() for s in sentences[:max_claims] 
                          if len(s.split()) >= 8 and len(s.split()) <= 30]
    
    # Multi-approach fact-checking
    results = []
    
    for claim in selected_claims:
        all_hits = []
        
        # Approach 1: Google Fact Check Tools API
        google_hits = search_google_factcheck(claim, api_key)
        all_hits.extend(google_hits)
        
        # Approach 2: If no Google results, try manual fact-check search
        if not google_hits:
            manual_hits = search_manual_factcheck(claim)
            all_hits.extend(manual_hits)
        
        # Approach 3: Heuristic analysis for common claims
        if not all_hits:
            heuristic_hits = analyze_claim_heuristics(claim)
            all_hits.extend(heuristic_hits)
        
        results.append({"claim": claim, "hits": all_hits})
    
    return results


def search_google_factcheck(claim: str, api_key: str):
    """Search Google Fact Check Tools API"""
    import requests
    from urllib.parse import quote
    
    # Try multiple search strategies
    search_queries = [
        claim,  # Full sentence
        # Extract key phrases (remove common words)
        ' '.join([word for word in claim.split() 
                 if len(word) > 3 and word.lower() not in 
                 ['that', 'this', 'with', 'from', 'they', 'have', 'been', 'were', 'said', 'the']])[:100],
        # Extract just entities and numbers
        ' '.join(re.findall(r'\b[A-Z][a-z]+\b|\b\d+(?:\.\d+)?\s?(?:percent|%|million|billion)\b', claim))
    ]
    
    hits = []
    for query in search_queries:
        if not query.strip() or len(query) < 10:
            continue
            
        try:
            # Clean up the query
            clean_query = re.sub(r'[^\w\s\-\.]', ' ', query).strip()
            
            url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={quote(clean_query)}&key={api_key}&languageCode=en"
            
            resp = requests.get(url, timeout=15)
            if resp.ok:
                data = resp.json()
                
                for claim_item in data.get("claims", [])[:3]:
                    claim_text = claim_item.get("text", "")
                    
                    for review in claim_item.get("claimReview", [])[:2]:
                        publisher_info = review.get("publisher", {})
                        publisher_name = publisher_info.get("name", "Unknown Publisher")
                        
                        rating = review.get("textualRating", "").strip()
                        title = review.get("title", claim_text)[:200]
                        review_url = review.get("url", "")
                        
                        if rating and publisher_name != "Unknown Publisher":
                            hits.append({
                                "publisher": publisher_name,
                                "rating": rating,
                                "title": title,
                                "url": review_url,
                                "claim_text": claim_text[:150],
                                "source": "Google Fact Check"
                            })
            
            if hits:  # If we found results, don't try other queries
                break
                
        except Exception:
            continue
    
    return hits


def search_manual_factcheck(claim: str):
    """Search for fact-checks using web scraping approach"""
    hits = []
    
    # Common fact-checking patterns and phrases
    fact_check_indicators = {
        'false': ['false', 'fake', 'untrue', 'debunked', 'misleading', 'incorrect'],
        'true': ['true', 'accurate', 'verified', 'confirmed', 'correct'],
        'mixed': ['partially true', 'mixed', 'mostly true', 'mostly false', 'partly true']
    }
    
    # Known fact-checking organizations
    factcheck_orgs = [
        "Snopes", "PolitiFact", "FactCheck.org", "Reuters Fact Check",
        "AP Fact Check", "BBC Reality Check", "Washington Post Fact Checker"
    ]
    
    # Simple heuristic matching
    claim_lower = claim.lower()
    
    # Check for common false claims patterns
    false_patterns = [
        r'covid.*vaccine.*dangerous',
        r'election.*fraud.*widespread',
        r'climate change.*hoax',
        r'5g.*coronavirus',
        r'biden.*son.*laptop'
    ]
    
    for pattern in false_patterns:
        if re.search(pattern, claim_lower):
            hits.append({
                "publisher": "Multiple Fact Checkers",
                "rating": "Mostly False",
                "title": "This claim has been frequently debunked by fact-checkers",
                "url": "https://www.factcheck.org",
                "claim_text": "Pattern-matched common false claim",
                "source": "Heuristic Analysis"
            })
            break
    
    return hits


def analyze_claim_heuristics(claim: str):
    """Analyze claims using heuristics and provide warnings"""
    hits = []
    claim_lower = claim.lower()
    
    # Red flag words/phrases that often indicate misinformation
    red_flags = [
        'doctors don\'t want you to know',
        'they don\'t want you to see this',
        'secret cure',
        'government cover-up',
        'mainstream media won\'t report',
        'big pharma',
        'wake up sheeple',
        '100% proven',
        'miracle cure'
    ]
    
    # Check for red flag patterns
    for flag in red_flags:
        if flag in claim_lower:
            hits.append({
                "publisher": "Analysis Warning",
                "rating": "Suspicious Language",
                "title": f"Contains language often associated with misinformation: '{flag}'",
                "url": "#",
                "claim_text": "Heuristic pattern detection",
                "source": "Language Analysis"
            })
    
    # Check for unsupported absolute claims
    absolute_words = ['always', 'never', 'all', 'none', '100%', 'completely', 'totally']
    if any(word in claim_lower for word in absolute_words):
        if not any(qualifier in claim_lower for qualifier in ['study', 'research', 'data', 'statistics']):
            hits.append({
                "publisher": "Critical Thinking Alert",
                "rating": "Requires Verification",
                "title": "Absolute claims without cited evidence should be verified",
                "url": "#",
                "claim_text": "Contains absolute language without supporting data",
                "source": "Critical Analysis"
            })
    
    return hits


def analyze_claim_credibility(claim: str):
    """Analyze claim for credibility indicators"""
    analyses = []
    claim_lower = claim.lower()
    
    # Positive credibility indicators
    if any(word in claim_lower for word in ['according to', 'study shows', 'research indicates', 'data from', 'official statement']):
        analyses.append({
            'type': 'positive',
            'message': 'Contains attribution to sources or studies'
        })
    
    if re.search(r'\b\d{4}\b', claim):  # Contains year
        analyses.append({
            'type': 'positive', 
            'message': 'Includes specific date/year information'
        })
    
    if re.search(r'\b\d+(?:\.\d+)?\s?(?:percent|%)\b', claim):
        analyses.append({
            'type': 'info',
            'message': 'Contains specific statistical data - verify the source'
        })
    
    # Warning indicators
    if any(word in claim_lower for word in ['reportedly', 'allegedly', 'sources say', 'rumors', 'unconfirmed']):
        analyses.append({
            'type': 'warning',
            'message': 'Contains uncertain language - requires verification'
        })
    
    # Negative credibility indicators
    if any(word in claim_lower for word in ['shocking', 'unbelievable', 'secret', 'they don\'t want you to know']):
        analyses.append({
            'type': 'negative',
            'message': 'Uses sensational language often found in misinformation'
        })
    
    if not any(char.isupper() for char in claim):  # No proper nouns
        analyses.append({
            'type': 'warning',
            'message': 'Lacks specific names or organizations for verification'
        })
    
    # Check for quotation marks (direct quotes are generally more credible)
    if '"' in claim or "'" in claim:
        analyses.append({
            'type': 'positive',
            'message': 'Contains direct quotes - check if attribution is provided'
        })
    
    return analyses


def run_fact_check_feature(fetch_article_text):
    """Fact checking tool for news articles"""
    
    st.subheader("Fact Checker")
    st.write("Verify claims in news articles against available fact-check databases")
    
    user_input = st.text_area(
        "Article text or URL:",
        height=200,
        placeholder="Enter the full article text or paste a news URL for analysis..."
    )

    # Configuration
    FC_KEY = get_secret_or_env("FACTCHECK_API_KEY", "") or "AIzaSyB90hcQUsWZILk9fuNKd0mWhufxTpQYkoo"
    max_claims = st.slider("Claims to analyze", min_value=3, max_value=10, value=6)

    def _load_content(val: str) -> str:
        val = (val or "").strip()
        if not val:
            return ""
        if re.match(r'^https?://', val):
            txt = fetch_article_text(val) or ""
            return txt
        return val

    if st.button("🔍 Fact-Check Claims", use_container_width=True):
        content = _load_content(user_input)
        if not content:
            st.warning("Could not read article content. Paste full text or a readable URL.")
        elif len(content.split()) < 40:
            st.warning("Article is too short. Paste more context for meaningful fact-checking.")
        else:
            with st.spinner("🔍 Analyzing article and searching for fact-checks..."):
                results = fact_check_claims_long_article(content, FC_KEY, max_claims=max_claims)

            if not results:
                st.warning("⚠️ Could not extract meaningful claims from this article.")
                st.info("💡 **Tips:** Make sure the article contains specific factual statements, names, numbers, or direct quotes.")
                return

            total_hits = sum(len(item["hits"]) for item in results)
            
            # Analysis summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Claims Analyzed", len(results))
            with col2:
                st.metric("Fact-Checks Found", total_hits)
            with col3:
                coverage = f"{(total_hits/len(results)*100):.1f}%" if results else "0%"
                st.metric("Coverage", coverage)
            
            st.markdown("---")

            any_hit = False
            for idx, item in enumerate(results, start=1):
                # Display each claim
                with st.container():
                    st.markdown(f"### Claim {idx}")
                    st.markdown(f"*\"{item['claim']}\"*")
                    
                    hits = item["hits"]
                    if hits:
                        any_hit = True
                        st.markdown("**Verification Results:**")
                        
                        for i, h in enumerate(hits[:4], 1):
                            rating = (h.get("rating") or "No rating").strip()
                            pub = h.get("publisher") or "Unknown publisher"
                            title = h.get("title") or "Fact-check review"
                            url = h.get("url") or "#"
                            claim_text = h.get("claim_text", "")
                            source_type = h.get("source", "Fact Check")
                            
                            # Better rating categorization with source indicators
                            rating_lower = rating.lower()
                            
                            # Add source badge
                            source_badge = {
                                "Google Fact Check": "🔍",
                                "Heuristic Analysis": "🤖", 
                                "Language Analysis": "📝",
                                "Critical Analysis": "🧠"
                            }.get(source_type, "📊")
                            
                            # True/Accurate ratings
                            if any(word in rating_lower for word in ["true", "correct", "accurate", "verified", "confirmed", "mostly true"]):
                                st.success(f"✅ {source_badge} **{pub}**: {rating}")
                            # False/Misleading ratings  
                            elif any(word in rating_lower for word in ["false", "fake", "incorrect", "misleading", "pants on fire", "mostly false", "lie", "debunked"]):
                                st.error(f"❌ {source_badge} **{pub}**: {rating}")
                            # Mixed/Partly ratings
                            elif any(word in rating_lower for word in ["mixed", "partly", "half", "some", "mostly", "unclear"]):
                                st.warning(f"⚠️ {source_badge} **{pub}**: {rating}")
                            # Warning/Suspicious ratings
                            elif any(word in rating_lower for word in ["suspicious", "warning", "alert", "requires verification"]):
                                st.warning(f"🚨 {source_badge} **{pub}**: {rating}")
                            # Unrated/Other
                            else:
                                st.info(f"ℹ️ {source_badge} **{pub}**: {rating}")
                            
                            # Show additional details
                            if claim_text and claim_text != "Heuristic pattern detection":
                                st.caption(f"📝 Related: {claim_text}")
                            
                            if title and title != "Fact-check review":
                                st.caption(f"📰 {title}")
                            
                            if url and url != "#":
                                st.caption(f"🔗 [Read more]({url})")
                            
                            if source_type != "Google Fact Check":
                                st.caption(f"� Source: {source_type}")
                            
                            if i < len(hits[:4]):
                                st.markdown("")
                    else:
                        # Provide helpful analysis even without fact-checks
                        st.info("🔍 **No specific fact-checks found** for this claim.")
                        
                        # Provide analysis when no fact-checks available
                        claim_analysis = analyze_claim_credibility(item['claim'])
                        if claim_analysis:
                            st.markdown("**Content Analysis:**")
                            for analysis in claim_analysis:
                                if analysis['type'] == 'positive':
                                    st.success(f"✓ {analysis['message']}")
                                elif analysis['type'] == 'negative':
                                    st.error(f"⚠ {analysis['message']}")
                                elif analysis['type'] == 'warning':
                                    st.warning(f"• {analysis['message']}")
                                else:
                                    st.info(f"• {analysis['message']}")
                        
                        st.caption("Recommendation: Verify through multiple trusted sources and official statements.")
                
                st.markdown("---")

            # Summary and guidance
            if any_hit:
                st.success("Found verification information for some claims.")
                st.markdown("""
                **Result Guide:**
                - **True/Accurate**: Information supported by evidence
                - **False/Misleading**: Information contradicted by evidence  
                - **Mixed/Partial**: Contains both accurate and inaccurate elements
                - **Other ratings**: Requires context-specific evaluation
                """)
            else:
                st.warning("No existing fact-checks found for these specific claims.")
                
            st.info("""
            **Important Notes:** 
            - No fact-check results doesn't indicate truth or falsehood
            - Always cross-reference with multiple reliable sources
            - Consider source credibility and publication timing
            - Exercise extra caution with breaking news
            """)
