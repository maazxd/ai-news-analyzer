"""
Translate News Feature
Translates news articles to different languages
"""
import streamlit as st
import re
from transformers import MarianMTModel, MarianTokenizer
from utils.helpers import detect_language


@st.cache_resource
def load_translation_model(src_lang, tgt_lang):
    """Load translation model for specific language pair"""
    model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model


def translate_text(text, src_lang, tgt_lang):
    """Translate text from source to target language"""
    tokenizer, model = load_translation_model(src_lang, tgt_lang)
    batch = tokenizer([text], return_tensors="pt", truncation=True, padding=True)
    gen = model.generate(**batch)
    return tokenizer.decode(gen[0], skip_special_tokens=True)


def get_article_text_or_content(user_input, fetch_article_text):
    """Get article text from URL or direct input"""
    # If input looks like a URL, try to fetch article text
    if re.match(r'https?://', user_input.strip()):
        article_text = fetch_article_text(user_input.strip())
        if article_text and len(article_text.split()) > 10:
            return article_text
        else:
            return None
    else:
        return user_input.strip()


def run_translate_feature(fetch_article_text):
    """Main function for Translate News feature"""
    
    st.subheader("🌐 Translate News Article or Link")
    user_input = st.text_area("Paste the news article content or a news article URL:", height=200)
    tgt_lang = st.selectbox(
        "Translate to",
        [("en", "English"), ("fr", "French"), ("de", "German"), ("es", "Spanish"), 
         ("it", "Italian"), ("ru", "Russian"), ("ar", "Arabic"), ("zh", "Chinese"), ("hi", "Hindi")],
        index=0,
        format_func=lambda x: x[1]
    )[0]

    if st.button("Translate", use_container_width=True):
        if user_input.strip():
            with st.spinner("Processing..."):
                content = get_article_text_or_content(user_input, fetch_article_text)
                if content:
                    detected_lang, detected_lang_name = detect_language(content)
                    st.info(f"**Detected Language:** {detected_lang_name} ({detected_lang})")
                    if detected_lang and detected_lang != tgt_lang:
                        try:
                            translation = translate_text(content, detected_lang, tgt_lang)
                            st.success("**Translation:**")
                            st.write(translation)
                        except Exception as e:
                            st.error(f"Translation failed: {e}")
                    elif detected_lang == tgt_lang:
                        st.info("Input and output languages are the same.")
                    else:
                        st.warning("Could not detect input language.")
                else:
                    st.error("Could not extract a valid article from the link. Please check the URL or try another article.")
        else:
            st.warning("Please enter news content or a news article URL to translate.")
