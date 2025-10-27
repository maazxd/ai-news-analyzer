"""
Article fetching utilities
"""
import newspaper


def fetch_article_text(url):
    """Fetch and extract text from news article URL"""
    try:
        article = newspaper.Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return ""
