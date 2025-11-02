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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
            script.decompose()
        
        # Try to find main content areas (expanded list for more sites)
        content_selectors = [
            'article', '[role="main"]', '.article-content', '.post-content', 
            '.entry-content', '.article-body', '.story-body', 'main',
            '.content', '.article', '.post', '.story', '.news-content',
            '#story-content', '#article-content', '.article-text',
            '.story-text', '[data-module="ArticleBody"]'
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
        
        # Validate that we got meaningful content
        if len(article_text) < 100:
            return ""
        
        return article_text
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return ""
    except Exception as e:
        print(f"Error extracting article: {e}")
        return ""
