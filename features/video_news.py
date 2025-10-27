"""
Video News Feature
Searches and displays YouTube news videos
"""
import streamlit as st
from typing import List, Dict
from googleapiclient.discovery import build


@st.cache_data(show_spinner=False)
def get_youtube_video_urls_by_language(query: str, api_key: str, lang_code: str = "any", max_results: int = 10) -> List[Dict]:
    """
    Search YouTube for news videos and filter by the video's default audio language if available.
    Falls back to relevanceLanguage hint during search. Not all videos expose language metadata.
    """
    youtube = build("youtube", "v3", developerKey=api_key)

    # Search more than needed so we can filter down by language
    search_kwargs = dict(
        q=f"{query} news",
        part="id",
        type="video",
        maxResults=min(max_results * 3, 50),
        safeSearch="strict"
    )
    if lang_code != "any":
        search_kwargs["relevanceLanguage"] = lang_code  # hint for search ranking

    search_resp = youtube.search().list(**search_kwargs).execute()
    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        return []

    vids_resp = youtube.videos().list(part="snippet", id=",".join(video_ids)).execute()
    results = []
    for item in vids_resp.get("items", []):
        sn = item["snippet"]
        audio_lang = sn.get("defaultAudioLanguage") or sn.get("defaultLanguage")  # ISO code like "en", "en-US", etc.
        keep = (lang_code == "any") or (audio_lang and audio_lang.split("-")[0] == lang_code)
        if keep:
            vid = item["id"]
            results.append({
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": sn.get("title", ""),
                "description": sn.get("description", ""),
                "channelTitle": sn.get("channelTitle", ""),
                "publishedAt": (sn.get("publishedAt", "") or "")[:10],
                "audioLang": audio_lang or "unknown"
            })

    # Limit to the requested number
    return results[:max_results]


def run_video_news_feature():
    """Main function for Video News feature"""
    
    st.subheader("🎥 Watch Latest Video News")

    # Filters row: topic, language, count
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        topic = st.text_input("Topic", "technology")
    with c2:
        # Language filter based on YouTube metadata
        lang_options = [
            ("any", "Any"),
            ("en", "English"),
            ("hi", "Hindi"),
            ("ar", "Arabic"),
            ("es", "Spanish"),
            ("fr", "French"),
            ("de", "German"),
            ("ru", "Russian"),
            ("pt", "Portuguese"),
            ("zh", "Chinese"),
            ("ja", "Japanese"),
        ]
        lang_code = st.selectbox("Video language", lang_options, index=0, format_func=lambda x: x[1])[0]
    with c3:
        num_videos = st.slider("Count", min_value=5, max_value=12, value=6)

    YT_API_KEY = "AIzaSyDUguThS4OPu-IxFnMBdHc19C5giRlbm4Q"
    
    if not topic.strip() or len(topic.strip()) < 3:
        st.warning("Enter a valid topic (min 3 characters).")
    else:
        with st.spinner("Searching videos..."):
            try:
                videos = get_youtube_video_urls_by_language(
                    topic, YT_API_KEY, lang_code=lang_code, max_results=num_videos
                )
                if videos:
                    for vid in videos:
                        video_id = vid["url"].split("v=")[-1]
                        thumb = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(
                                f'<a href="{vid["url"]}" target="_blank">'
                                f'<img src="{thumb}" width="160" style="border-radius:8px;"/></a>',
                                unsafe_allow_html=True
                            )
                        with col2:
                            st.markdown(f"**[{vid['title']}]({vid['url']})**")
                            st.caption(f"Channel: {vid.get('channelTitle','N/A')} • Date: {vid.get('publishedAt','N/A')} • Lang: {vid.get('audioLang','unknown')}")
                        st.markdown("---")
                else:
                    msg = "No videos matched the language filter." if lang_code != "any" else "No videos found for this topic."
                    st.info(msg + " Try a different language or broader topic.")
                    if lang_code != "any":
                        st.caption("Note: Language filtering relies on YouTube metadata and is not available for all videos.")
            except Exception as e:
                st.error(f"Failed to fetch videos: {e}")
