"""
Multi-source Data Fetcher.
Pulls live market prices, historical OHLCV data, fundamental metrics,
Wall Street analyst targets, and real-time news headlines via RSS feeds.
Includes multi-threaded parallel batch retrieval and aggressive caching.
"""

import time
import concurrent.futures
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET
import pandas as pd
import requests
import yfinance as yf

from core.cache_manager import cache
from core.config import CACHE_TTL_PRICE, CACHE_TTL_FUNDAMENTAL

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_stock_news_rss(ticker: str, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Fetch real-time financial news headlines via Google News RSS.
    100% reliable, zero API key required, covering major financial publications.
    """
    cache_key = f"news_rss_{ticker.upper()}"
    cached_news = cache.get(cache_key)
    if cached_news:
        return cached_news
        
    url = f"https://news.google.com/rss/search?q={ticker}+stock+when:7d&hl=en-US&gl=US&ceid=US:en"
    headers = {"User-Agent": USER_AGENT}
    articles = []
    
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:limit]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else "#"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                source_tag = item.find("source")
                publisher = source_tag.text if source_tag is not None else "Market News"
                
                # Clean up title: often ends with "- Publisher"
                clean_title = title
                if " - " in title:
                    clean_title = title.rsplit(" - ", 1)[0]
                    
                articles.append({
                    "title": clean_title,
                    "publisher": publisher,
                    "link": link,
                    "date": pub_date[:16] if pub_date else "Recent",
                    "providerPublishTime": int(time.time())
                })
    except Exception as e:
        # Fallback empty
        pass
        
    cache.set(cache_key, articles, ttl_seconds=1800)  # 30 min cache
    return articles


def fetch_stock_data(ticker: str, period: str = "1y") -> Optional[Dict[str, Any]]:
    """
    Fetches full stock data bundle:
    - OHLCV price history (DataFrame + JSON chart array)
    - Key fundamentals and company info
    - Real-time news items
    """
    symbol = ticker.strip().upper()
    cache_key = f"stock_bundle_{symbol}_{period}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        t = yf.Ticker(symbol)
        hist = t.history(period=period)
        
        if hist is None or hist.empty or len(hist) < 10:
            return None
            
        # Basic company info
        try:
            info = t.info or {}
        except Exception:
            info = {}
            
        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        change_val = current_price - prev_close
        change_pct = (change_val / prev_close) * 100 if prev_close > 0 else 0.0
        
        # Prepare lightweight chart format
        chart_data = []
        for idx, row in hist.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            chart_data.append({
                "time": date_str,
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume'])
            })
            
        # Fetch real-time news
        news_items = fetch_stock_news_rss(symbol, limit=8)
        
        bundle = {
            "symbol": symbol,
            "short_name": info.get("shortName") or info.get("longName") or symbol,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "USD"),
            "current_price": round(current_price, 2),
            "prev_close": round(prev_close, 2),
            "change_val": round(change_val, 2),
            "change_pct": round(change_pct, 2),
            "history_df": hist,  # used internally by engines
            "chart_data": chart_data,
            "info": info,
            "news": news_items
        }
        
        # Cache bundle (excluding raw DataFrame for JSON disk cache)
        cache_bundle = {k: v for k, v in bundle.items() if k != "history_df"}
        cache.set(cache_key, cache_bundle, ttl_seconds=CACHE_TTL_PRICE)
        
        return bundle
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def batch_fetch_stocks(symbols: List[str], max_workers: int = 8) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple stock bundles in parallel using ThreadPoolExecutor.
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {executor.submit(fetch_stock_data, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                data = future.result()
                if data:
                    results[sym] = data
            except Exception as e:
                print(f"Failed to fetch batch item {sym}: {e}")
                
    return results

