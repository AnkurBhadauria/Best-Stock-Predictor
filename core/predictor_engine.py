"""
Stock Prediction and Horizon Ranking Engine.
Synthesizes technical indicators, fundamental health, analyst consensus,
and news sentiment into horizon-specific prediction models (1-2 Weeks, 1-2 Months, 1-2 Years).
Calculates expected returns, win probabilities, entry/stop/target prices, and ranks the best stocks.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from core.technical_engine import analyze_technicals
from core.fundamental_engine import analyze_fundamentals
from core.sentiment_engine import analyze_news_sentiment
from core.config import HORIZONS, SCREENING_UNIVERSE
from core.data_fetcher import fetch_stock_data, batch_fetch_stocks
from core.cache_manager import cache


def estimate_projected_return(current_price: float, score: float, horizon_key: str, technicals: Dict[str, Any], fundamentals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes statistical expected return range and target price based on
    factor score, historical volatility (ATR), and analyst estimates.
    """
    atr_pct = technicals.get("atr_pct", 2.5) if technicals.get("valid") else 2.5
    analyst_upside = fundamentals.get("analyst_consensus", {}).get("upside_pct", 0.0) if fundamentals.get("valid") else 0.0
    
    # Base multipliers tied to score (score normalized from 50)
    score_alpha = (score - 50.0) / 50.0  # -1.0 to +1.0
    
    if horizon_key == "short_term":
        # 1-2 Weeks: driven by ATR moves and momentum volatility
        # Expected return typically 3% to 15%
        expected_move_pct = max(1.5, min(18.0, (atr_pct * 2.2) * (1.0 + (score_alpha * 0.7))))
        min_return = round(expected_move_pct * 0.6, 2)
        max_return = round(expected_move_pct * 1.4, 2)
        target_return = round(expected_move_pct, 2)
        target_price = round(current_price * (1 + target_return / 100), 2)
        timeframe_label = "1-2 Weeks (10 Trading Days)"
        
    elif horizon_key == "medium_term":
        # 1-2 Months: blend of quarterly momentum and analyst upside
        base_medium = (atr_pct * 4.5) * (1.0 + (score_alpha * 0.8))
        if analyst_upside > 0:
            blended = (base_medium * 0.6) + (analyst_upside * 0.4 * 0.4)
        else:
            blended = base_medium
        target_return = round(max(4.0, min(35.0, blended)), 2)
        min_return = round(target_return * 0.7, 2)
        max_return = round(target_return * 1.35, 2)
        target_price = round(current_price * (1 + target_return / 100), 2)
        timeframe_label = "1-2 Months (45 Trading Days)"
        
    else:  # long_term
        # 1-2 Years: driven by ROE, revenue growth, and Wall Street target
        rev_growth = fundamentals.get("metrics", {}).get("revenue_growth", 10.0) or 10.0
        roe = fundamentals.get("metrics", {}).get("roe", 15.0) or 15.0
        
        # Long-term compounding formula
        compound_rate = (rev_growth * 0.4) + (roe * 0.3) + 8.0
        if analyst_upside > 0:
            target_return = round(max(15.0, min(95.0, (compound_rate * 0.6) + (analyst_upside * 0.4))), 2)
        else:
            target_return = round(max(15.0, min(80.0, compound_rate * (1.0 + score_alpha * 0.5))), 2)
            
        min_return = round(target_return * 0.75, 2)
        max_return = round(target_return * 1.4, 2)
        target_price = round(current_price * (1 + target_return / 100), 2)
        timeframe_label = "1-2 Years (Long Term)"
        
    return {
        "timeframe": timeframe_label,
        "target_return_pct": target_return,
        "range_min_pct": min_return,
        "range_max_pct": max_return,
        "target_price": target_price
    }


def evaluate_stock(stock_bundle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evaluates a stock across Technicals, Fundamentals, Sentiment,
    and calculates Horizon-Specific Scores & Predictions.
    """
    if not stock_bundle:
        return None
        
    symbol = stock_bundle["symbol"]
    current_price = stock_bundle["current_price"]
    hist_df = stock_bundle.get("history_df")
    
    # If hist_df not stored in memory cache, re-fetch or reconstruct
    if hist_df is None or not isinstance(hist_df, pd.DataFrame):
        import yfinance as yf
        t = yf.Ticker(symbol)
        hist_df = t.history(period="1y")
        
    info = stock_bundle.get("info", {})
    news_items = stock_bundle.get("news", [])
    
    # 1. Technical Analysis
    tech_results = analyze_technicals(hist_df)
    
    # 2. Fundamental Analysis
    fund_results = analyze_fundamentals(info)
    
    # 3. Sentiment Analysis
    sent_results = analyze_news_sentiment(news_items)
    
    # Pull scores
    tech_st_score = tech_results.get("short_term_score", 50.0) if tech_results.get("valid") else 50.0
    tech_mt_score = tech_results.get("medium_term_score", 50.0) if tech_results.get("valid") else 50.0
    fund_score = fund_results.get("quality_score", 50.0) if fund_results.get("valid") else 50.0
    sent_score = sent_results.get("score", 50.0)
    
    # Factor Breakdown Matrix
    factor_breakdown = {
        "technical_momentum": round(tech_st_score, 1),
        "fundamental_quality": round(fund_score, 1),
        "news_sentiment": round(sent_score, 1),
        "trend_strength": round(tech_mt_score, 1),
        "analyst_conviction": round(max(20.0, min(95.0, 50.0 + (fund_results.get("analyst_consensus", {}).get("upside_pct", 0) * 1.2))), 1)
    }
    
    # -------------------------------------------------------------
    # HORIZON 1: Short-Term (1-2 Weeks) Prediction Model
    # -------------------------------------------------------------
    # Weights: Technical Momentum (45%), Volume/Breakout (20%), Sentiment (20%), Risk (15%)
    vol_ratio = tech_results.get("volume_surge_ratio", 1.0) if tech_results.get("valid") else 1.0
    vol_pts = min(20.0, (vol_ratio - 1.0) * 20.0) if vol_ratio > 1.0 else (vol_ratio - 1.0) * 10.0
    
    raw_st = (tech_st_score * 0.50) + (sent_score * 0.25) + (50.0 + vol_pts) * 0.25
    st_score = round(max(10.0, min(99.0, raw_st)), 1)
    
    st_projection = estimate_projected_return(current_price, st_score, "short_term", tech_results, fund_results)
    
    # Short-Term Win Probability (Quant estimation based on score)
    st_win_prob = round(min(94.0, max(42.0, 50.0 + (st_score - 50.0) * 0.75)), 1)
    
    # Short-Term Action Signal
    if st_score >= 82:
        st_signal = "STRONG BUY (Breakout)"
        st_badge = "badge-strong-buy"
    elif st_score >= 70:
        st_signal = "BUY (Momentum)"
        st_badge = "badge-buy"
    elif st_score >= 55:
        st_signal = "WATCHLIST (Consolidating)"
        st_badge = "badge-hold"
    else:
        st_signal = "NEUTRAL / WAIT"
        st_badge = "badge-neutral"
        
    st_reasons = []
    if tech_results.get("valid"):
        for s in tech_results.get("signals", [])[:3]:
            st_reasons.append(s["text"])
    if sent_results.get("sentiment_label") in ["BULLISH", "VERY BULLISH"]:
        st_reasons.append(f"Bullish news sentiment polarity ({sent_results.get('sentiment_label')})")
        
    # -------------------------------------------------------------
    # HORIZON 2: Medium-Term (1-2 Months) Prediction Model
    # -------------------------------------------------------------
    # Weights: Trend Continuation (35%), Earnings/Fundamentals (30%), Analyst Upside (20%), Sentiment (15%)
    raw_mt = (tech_mt_score * 0.35) + (fund_score * 0.30) + (factor_breakdown["analyst_conviction"] * 0.20) + (sent_score * 0.15)
    mt_score = round(max(10.0, min(99.0, raw_mt)), 1)
    
    mt_projection = estimate_projected_return(current_price, mt_score, "medium_term", tech_results, fund_results)
    mt_win_prob = round(min(92.0, max(40.0, 50.0 + (mt_score - 50.0) * 0.70)), 1)
    
    if mt_score >= 80:
        mt_signal = "STRONG BUY (Trend & Growth)"
        mt_badge = "badge-strong-buy"
    elif mt_score >= 68:
        mt_signal = "BUY (Swing Continuation)"
        mt_badge = "badge-buy"
    elif mt_score >= 54:
        mt_signal = "ACCUMULATE ON DIPS"
        mt_badge = "badge-hold"
    else:
        mt_signal = "HOLD / NEUTRAL"
        mt_badge = "badge-neutral"
        
    mt_reasons = []
    if tech_results.get("valid"):
        if current_price > tech_results.get("sma_50", 0):
            mt_reasons.append(f"Trading firmly above 50-day SMA (${tech_results.get('sma_50')})")
        if tech_results.get("returns", {}).get("60d", 0) > 0:
            mt_reasons.append(f"+{tech_results.get('returns', {}).get('60d')}% gain over last 60 days")
    if fund_results.get("valid"):
        analyst_up = fund_results.get("analyst_consensus", {}).get("upside_pct", 0)
        if analyst_up > 5:
            mt_reasons.append(f"Wall Street target implies +{analyst_up}% upside")
            
    # -------------------------------------------------------------
    # HORIZON 3: Long-Term (1-2 Years) Prediction Model
    # -------------------------------------------------------------
    # Weights: Fundamental Quality/ROE (40%), Valuation/PEG (30%), Wall St Consensus (20%), Solvency (10%)
    raw_lt = (fund_score * 0.50) + (factor_breakdown["analyst_conviction"] * 0.25) + (tech_mt_score * 0.15) + (sent_score * 0.10)
    lt_score = round(max(10.0, min(99.0, raw_lt)), 1)
    
    lt_projection = estimate_projected_return(current_price, lt_score, "long_term", tech_results, fund_results)
    lt_win_prob = round(min(95.0, max(45.0, 50.0 + (lt_score - 50.0) * 0.80)), 1)
    
    if lt_score >= 80:
        lt_signal = "TOP COMPOUNDER (Conviction Buy)"
        lt_badge = "badge-strong-buy"
    elif lt_score >= 68:
        lt_signal = "LONG-TERM BUY (Quality Growth)"
        lt_badge = "badge-buy"
    elif lt_score >= 52:
        lt_signal = "DCA CANDIDATE (Dollar-Cost Average)"
        lt_badge = "badge-hold"
    else:
        lt_signal = "UNDERWEIGHT / CAUTION"
        lt_badge = "badge-neutral"
        
    lt_reasons = []
    if fund_results.get("valid"):
        for s in fund_results.get("signals", [])[:3]:
            lt_reasons.append(s["text"])
        lt_reasons.append(f"Valuation Assessment: {fund_results.get('valuation_verdict')}")
        
    # Trade Setup from Technical Engine (Entry, Stop Loss, Target 1, Target 2)
    trade_setup = tech_results.get("trade_setup", {
        "entry_price": current_price,
        "stop_loss": round(current_price * 0.95, 2),
        "take_profit_1": round(current_price * 1.08, 2),
        "take_profit_2": round(current_price * 1.15, 2),
        "risk_reward_ratio": 2.5,
        "risk_pct": 5.0,
        "target_pct_tp1": 8.0,
        "target_pct_tp2": 15.0
    })
    
    return {
        "symbol": symbol,
        "name": stock_bundle.get("short_name", symbol),
        "sector": stock_bundle.get("sector", "N/A"),
        "industry": stock_bundle.get("industry", "N/A"),
        "currency": stock_bundle.get("currency", "USD"),
        "current_price": current_price,
        "change_pct": stock_bundle.get("change_pct", 0.0),
        "change_val": stock_bundle.get("change_val", 0.0),
        "factors": factor_breakdown,
        "horizons": {
            "short_term": {
                "score": st_score,
                "signal": st_signal,
                "badge": st_badge,
                "win_probability": st_win_prob,
                "projection": st_projection,
                "key_reasons": st_reasons[:4],
                "trade_setup": trade_setup
            },
            "medium_term": {
                "score": mt_score,
                "signal": mt_signal,
                "badge": mt_badge,
                "win_probability": mt_win_prob,
                "projection": mt_projection,
                "key_reasons": mt_reasons[:4],
                "trailing_stop": round(current_price * 0.92, 2)
            },
            "long_term": {
                "score": lt_score,
                "signal": lt_signal,
                "badge": lt_badge,
                "win_probability": lt_win_prob,
                "projection": lt_projection,
                "key_reasons": lt_reasons[:4],
                "quality_grade": fund_results.get("quality_grade", "A")
            }
        },
        "technicals": tech_results,
        "fundamentals": fund_results,
        "sentiment": sent_results,
        "chart_data": stock_bundle.get("chart_data", [])[-90:]  # last 90 candles for charts
    }


def get_ranked_recommendations(horizon: str = "short_term", custom_universe: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ranks all stocks in universe for the specified horizon:
    'short_term' (1-2 weeks), 'medium_term' (1-2 months), 'long_term' (1-2 years).
    Returns ranked leaderboard and #1 Spotlight Stock.
    """
    cache_key = f"ranked_recommendations_{horizon}"
    cached = cache.get(cache_key)
    if cached and not custom_universe:
        return cached

    universe = custom_universe or SCREENING_UNIVERSE[:25]  # Top liquid screen list
    
    # Batch fetch in parallel
    bundles = batch_fetch_stocks(universe, max_workers=8)
    
    evaluated_stocks = []
    for sym, bundle in bundles.items():
        try:
            eval_res = evaluate_stock(bundle)
            if eval_res:
                evaluated_stocks.append(eval_res)
        except Exception as e:
            print(f"Error evaluating {sym}: {e}")
            
    if not evaluated_stocks:
        return {
            "horizon": horizon,
            "horizon_meta": HORIZONS.get(horizon, {}),
            "spotlight_stock": None,
            "leaderboard": [],
            "total_analyzed": 0
        }
        
    # Sort stocks by specific horizon score descending
    evaluated_stocks.sort(
        key=lambda s: (
            s["horizons"].get(horizon, {}).get("score", 0),
            s["horizons"].get(horizon, {}).get("projection", {}).get("target_return_pct", 0)
        ),
        reverse=True
    )
    
    # Assign ranks
    for rank, stock in enumerate(evaluated_stocks, start=1):
        stock["rank"] = rank
        
    spotlight = evaluated_stocks[0] if evaluated_stocks else None
    
    result = {
        "horizon": horizon,
        "horizon_meta": HORIZONS.get(horizon, {}),
        "spotlight_stock": spotlight,
        "leaderboard": evaluated_stocks,
        "total_analyzed": len(evaluated_stocks)
    }
    
    if not custom_universe:
        cache.set(cache_key, result, ttl_seconds=1200)  # 20 min cache
        
    return result

