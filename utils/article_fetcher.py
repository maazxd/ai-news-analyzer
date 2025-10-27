"""
Article fetching utilities
"""
import requests
from bs4 import BeautifulSoup
import re


def fetch_article_text(url):
    """Fetch and extract text from news article URL"""
    try:
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'article', '[role="main"]', '.article-content', '.post-content', 
            '.entry-content', '.article-body', '.story-body', 'main'
        ]
        
        article_text = ""
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                article_text = content_div.get_text()
                break
        
        # Fallback: get all paragraph text
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text() for p in paragraphs])
        
        # Clean up the text
        article_text = re.sub(r'\s+', ' ', article_text).strip()
        
        return article_text
        
    except Exception as e:
        return ""
