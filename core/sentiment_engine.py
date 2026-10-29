"""
News & Sentiment Engine.
Extracts recent news headlines and applies financial sentiment scoring
to identify breaking catalysts, narrative momentum, and market polarity.
"""

from typing import List, Dict, Any
import re
from datetime import datetime

# Financial sentiment lexicon with polarity weights
BULLISH_KEYWORDS = {
    "surge": 2.0, "soar": 2.0, "skyrocket": 2.5, "jump": 1.5, "rally": 1.8, "breakout": 2.2,
    "beat": 1.8, "crushed": 2.0, "record": 1.5, "outperform": 1.8, "upgrade": 2.0, "upgrades": 2.0,
    "bull": 1.5, "bullish": 1.8, "growth": 1.2, "accelerate": 1.5, "buy": 1.2, "strong buy": 2.2,
    "profit": 1.2, "partnership": 1.5, "all-time high": 2.2, "expansion": 1.3, "dividend hike": 1.7,
    "patent": 1.4, "approval": 2.0, "gain": 1.2, "boost": 1.5, "upside": 1.5, "catalyst": 1.4,
    "breakthrough": 2.0, "dominant": 1.5, "momentum": 1.5, "raises guidance": 2.5, "raises forecast": 2.5
}

BEARISH_KEYWORDS = {
    "slump": -2.0, "plunge": -2.2, "tumble": -2.0, "crash": -2.5, "drop": -1.2, "fall": -1.0,
    "miss": -1.8, "misses": -1.8, "downgrade": -2.0, "downgrades": -2.0, "bear": -1.5, "bearish": -1.8,
    "lawsuit": -2.0, "investigation": -2.2, "probe": -2.0, "sec": -1.5, "cut": -1.5, "layoffs": -1.8,
    "deficit": -1.5, "debt crisis": -2.5, "warning": -1.8, "guidance cut": -2.5, "sell": -1.5,
    "loss": -1.2, "disappoints": -2.0, "struggle": -1.5, "weakness": -1.5, "risk": -1.0,
    "headwind": -1.4, "scandal": -2.5, "bankruptcy": -3.0, "default": -2.5, "selloff": -2.0
}


def score_text(text: str) -> float:
    """Calculates weighted sentiment score for a piece of text."""
    if not text:
        return 0.0
    text_lower = text.lower()
    score = 0.0
    
    for kw, weight in BULLISH_KEYWORDS.items():
        # Match whole word or phrase
        pattern = r'\b' + re.escape(kw) + r'\b'
        matches = len(re.findall(pattern, text_lower))
        if matches > 0:
            score += weight * matches
            
    for kw, weight in BEARISH_KEYWORDS.items():
        pattern = r'\b' + re.escape(kw) + r'\b'
        matches = len(re.findall(pattern, text_lower))
        if matches > 0:
            score += weight * matches  # weight is already negative
            
    return score


def analyze_news_sentiment(news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes list of news items returned by yfinance.
    Produces composite sentiment polarity (-100 to +100), label, and formatted catalysts.
    """
    if not news_items:
        return {
            "score": 50.0,
            "sentiment_label": "NEUTRAL",
            "polarity": 0.0,
            "headline_count": 0,
            "recent_catalysts": []
        }
        
    scored_articles = []
    total_score = 0.0
    
    for item in news_items[:10]:  # analyze up to 10 most recent news
        title = item.get("title", "")
        # Some yfinance versions use content / summary
        summary = item.get("summary", "") or ""
        publisher = item.get("publisher", "Financial News")
        link = item.get("link", "#")
        provider_pub_time = item.get("providerPublishTime")
        
        pub_date_str = ""
        if provider_pub_time:
            try:
                pub_date_str = datetime.fromtimestamp(provider_pub_time).strftime('%b %d, %Y')
            except Exception:
                pub_date_str = "Recent"
                
        # Score title higher as it captures the primary sentiment
        title_score = score_text(title) * 1.5
        summary_score = score_text(summary)
        item_score = title_score + summary_score
        
        total_score += item_score
        
        if item_score > 0.5:
            sentiment = "BULLISH"
        elif item_score < -0.5:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
            
        scored_articles.append({
            "title": title,
            "publisher": publisher,
            "link": link,
            "date": pub_date_str,
            "sentiment": sentiment,
            "score": round(item_score, 2)
        })
        
    # Normalize score to 0 - 100 range (50 is neutral)
    # Using tanh-like scaling for polarity
    avg_score = total_score / max(1, len(scored_articles))
    normalized_score = round(50.0 + (min(max(avg_score, -5.0), 5.0) / 5.0) * 45.0, 1)
    
    if normalized_score >= 70:
        sentiment_label = "VERY BULLISH"
    elif normalized_score >= 58:
        sentiment_label = "BULLISH"
    elif normalized_score <= 35:
        sentiment_label = "VERY BEARISH"
    elif normalized_score <= 45:
        sentiment_label = "BEARISH"
    else:
        sentiment_label = "NEUTRAL"
        
    return {
        "score": normalized_score,
        "sentiment_label": sentiment_label,
        "polarity": round(avg_score, 2),
        "headline_count": len(scored_articles),
        "recent_catalysts": scored_articles
    }

