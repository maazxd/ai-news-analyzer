"""
Source credibility and political leaning databases
"""
import tldextract


# ========== SOURCE CREDIBILITY ==========
SOURCE_CREDIBILITY = {
    # Global
    "bbc.com": ("High Credibility", "UK public broadcaster."),
    "bbc.co.uk": ("High Credibility", "UK public broadcaster."),
    "reuters.com": ("High Credibility", "International wire service."),
    "apnews.com": ("High Credibility", "Associated Press wire service."),
    "theguardian.com": ("High Credibility", "Major UK newspaper."),
    "nytimes.com": ("High Credibility", "Major US newspaper."),
    "wsj.com": ("High Credibility", "Major US business newspaper."),
    "cnn.com": ("Mixed Credibility", "Mainstream US cable news; opinion-heavy shows."),
    "foxnews.com": ("Mixed Credibility", "US cable news; strong opinion content."),
    "aljazeera.com": ("High Credibility", "International news network."),
    "theonion.com": ("Satire", "Well‑known satire site."),
    "infowars.com": ("Questionable", "Conspiracy content and misinformation."),

    # India – national dailies / networks
    "thehindu.com": ("High Credibility", "Leading Indian national daily."),
    "hindustantimes.com": ("High Credibility", "Major Indian newspaper."),
    "indianexpress.com": ("High Credibility", "The Indian Express Group."),
    "newindianexpress.com": ("High Credibility", "Established Indian newspaper."),
    "livemint.com": ("High Credibility", "Mint — business/markets coverage."),
    "business-standard.com": ("High Credibility", "Business Standard newspaper."),
    "theprint.in": ("Mixed Credibility", "Analysis‑heavy digital outlet."),
    "thewire.in": ("Mixed Credibility", "Investigative outlet; some controversies."),
    "scroll.in": ("Mixed Credibility", "Indian digital news magazine."),
    "indiatoday.in": ("High Credibility", "India Today Group."),
    "deccanherald.com": ("High Credibility", "Deccan Herald newspaper."),
    "news18.com": ("Mixed Credibility", "Network18 news network."),
    "ndtv.com": ("Mixed Credibility", "Mainstream Indian news network credibility diluted after Adani acquisition."),
    "opindia.com": ("Questionable", "Far-right organization known for bias and misinformation."),

    # Times Group domains (subdomain‑specific + base)
    "economictimes.indiatimes.com": ("High Credibility", "The Economic Times (business)."),
    "timesofindia.indiatimes.com": ("High Credibility", "The Times of India."),
    "indiatimes.com": ("Mixed Credibility", "Parent domain for multiple brands."),

    # Zee / Times Now (subdomains)
    "zeenews.india.com": ("Mixed Credibility", "Zee News network site."),
    "timesnownews.com": ("Mixed Credibility", "Times Now network site."),
}


# Simple mapping for demonstration; expand as needed
SOURCE_POLITICAL_LEANING = {
    # Global
    "reuters.com": "center",
    "apnews.com": "center",
    "bbc.com": "center",
    "bbc.co.uk": "center",
    "theguardian.com": "left-leaning",
    "nytimes.com": "left-leaning",
    "wsj.com": "right-leaning",   # news center; editorial right-leaning
    "cnn.com": "left-leaning",
    "foxnews.com": "right-leaning",
    "aljazeera.com": "center",

    # India
    "thehindu.com": "left-leaning",
    "hindustantimes.com": "center",
    "indianexpress.com": "center",
    "newindianexpress.com": "center",
    "livemint.com": "center",
    "business-standard.com": "center",
    "theprint.in": "center",
    "thewire.in": "left-leaning",
    "scroll.in": "left-leaning",
    "indiatoday.in": "center",
    "deccanherald.com": "center",
    "news18.com": "right-leaning",
    "ndtv.com": "right-leaning", 
    "opindia.com": "far-right",

    # Times Group (subdomain‑specific + base)
    "economictimes.indiatimes.com": "center",
    "timesofindia.indiatimes.com": "center",
    "indiatimes.com": "center",

    # Zee / Times Now
    "zeenews.india.com": "right-leaning",
    "timesnownews.com": "right-leaning",
}


def get_source_credibility(url):
    """Get credibility rating for a news source URL"""
    ext = tldextract.extract(url)
    base = f"{ext.domain}.{ext.suffix}"
    full = f"{ext.subdomain}.{base}" if ext.subdomain else base
    return SOURCE_CREDIBILITY.get(full) or SOURCE_CREDIBILITY.get(
        base, ("Unknown", "No credibility information available for this source.")
    )


def get_source_political_leaning(url):
    """Get political leaning for a news source URL"""
    ext = tldextract.extract(url)
    base = f"{ext.domain}.{ext.suffix}"
    full = f"{ext.subdomain}.{base}" if ext.subdomain else base
    return SOURCE_POLITICAL_LEANING.get(full) or SOURCE_POLITICAL_LEANING.get(base, "unknown")
