"""
Fundamental Analysis Engine.
Analyzes corporate earnings, valuation multiples (P/E, PEG, EV/EBITDA),
margins, ROE, debt-to-equity, free cash flow, and Wall Street analyst targets.
Produces Long-Term and Medium-Term fundamental quality scores.
"""

from typing import Dict, Any, Optional


def analyze_fundamentals(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform deep fundamental analysis on ticker information dictionary.
    Returns ratios, quality score (0-100), valuation verdict, and qualitative signals.
    """
    if not info:
        return {
            "valid": False,
            "error": "No fundamental data available"
        }
    
    current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0
    
    # Valuation Metrics
    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    peg_ratio = info.get("pegRatio")
    price_to_book = info.get("priceToBook")
    price_to_sales = info.get("priceToSalesTrailing12Months")
    ev_to_ebitda = info.get("enterpriseToEbitda")
    
    # Profitability & Efficiency
    profit_margins = info.get("profitMargins")
    operating_margins = info.get("operatingMargins")
    gross_margins = info.get("grossMargins")
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    
    # Growth
    earnings_growth = info.get("earningsGrowth")
    revenue_growth = info.get("revenueGrowth")
    
    # Financial Health & Balance Sheet
    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    free_cashflow = info.get("freeCashflow")
    
    # Dividend
    dividend_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")
    
    # Analyst Ratings & Targets
    target_mean_price = info.get("targetMeanPrice")
    target_high_price = info.get("targetHighPrice")
    target_low_price = info.get("targetLowPrice")
    target_median_price = info.get("targetMedianPrice") or target_mean_price
    num_analysts = info.get("numberOfAnalystOpinions") or 0
    recommendation_key = info.get("recommendationKey", "none").replace("_", " ").title()
    recommendation_mean = info.get("recommendationMean")  # 1.0 (Strong Buy) to 5.0 (Strong Sell)
    
    # Calculate Wall Street Target Upside %
    analyst_upside_pct = 0.0
    if target_mean_price and current_price and current_price > 0:
        analyst_upside_pct = round(((target_mean_price - current_price) / current_price) * 100, 2)
        
    signals = []
    long_term_score = 50.0  # baseline
    
    # 1. Profitability & ROE (Up to +25 pts)
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct >= 25:
            long_term_score += 20
            signals.append({"type": "BULLISH", "text": f"Exceptional Return on Equity (ROE: {roe_pct:.1f}%)"})
        elif roe_pct >= 15:
            long_term_score += 12
            signals.append({"type": "BULLISH", "text": f"Healthy Return on Equity (ROE: {roe_pct:.1f}%)"})
        elif roe_pct < 5:
            long_term_score -= 10
            signals.append({"type": "BEARISH", "text": f"Weak Return on Equity (ROE: {roe_pct:.1f}%)"})
            
    if profit_margins is not None:
        margin_pct = profit_margins * 100
        if margin_pct >= 20:
            long_term_score += 10
            signals.append({"type": "BULLISH", "text": f"High Net Profit Margin ({margin_pct:.1f}%)"})
        elif margin_pct < 0:
            long_term_score -= 15
            signals.append({"type": "CAUTION", "text": "Currently Unprofitable (Negative Margins)"})
            
    # 2. Valuation & PEG (Up to +25 pts)
    if peg_ratio is not None and peg_ratio > 0:
        if peg_ratio < 1.0:
            long_term_score += 18
            signals.append({"type": "BULLISH", "text": f"High Growth at a Bargain (PEG: {peg_ratio:.2f} < 1.0)"})
        elif peg_ratio < 1.8:
            long_term_score += 10
            signals.append({"type": "BULLISH", "text": f"Reasonable Valuation Multiple (PEG: {peg_ratio:.2f})"})
        elif peg_ratio > 3.5:
            long_term_score -= 10
            signals.append({"type": "CAUTION", "text": f"Stretched Growth Valuation (PEG: {peg_ratio:.2f})"})
    elif forward_pe is not None and trailing_pe is not None:
        if forward_pe < trailing_pe * 0.85:
            long_term_score += 10
            signals.append({"type": "BULLISH", "text": f"Forward P/E discount ({forward_pe:.1f} vs {trailing_pe:.1f})"})
            
    # 3. Growth Trajectory (Up to +20 pts)
    if revenue_growth is not None:
        rev_growth_pct = revenue_growth * 100
        if rev_growth_pct >= 20:
            long_term_score += 12
            signals.append({"type": "BULLISH", "text": f"Rapid Revenue Growth ({rev_growth_pct:+.1f}% YoY)"})
        elif rev_growth_pct > 8:
            long_term_score += 6
        elif rev_growth_pct < -5:
            long_term_score -= 10
            signals.append({"type": "BEARISH", "text": f"Declining Revenue ({rev_growth_pct:.1f}% YoY)"})
            
    if earnings_growth is not None:
        eps_growth_pct = earnings_growth * 100
        if eps_growth_pct >= 25:
            long_term_score += 12
            signals.append({"type": "BULLISH", "text": f"Surging Quarterly Earnings ({eps_growth_pct:+.1f}% YoY)"})
            
    # 4. Solvency & Cash Flow (Up to +15 pts)
    if debt_to_equity is not None:
        if debt_to_equity < 50:
            long_term_score += 10
            signals.append({"type": "BULLISH", "text": "Pristine Balance Sheet (Low Debt/Equity)"})
        elif debt_to_equity > 200:
            long_term_score -= 12
            signals.append({"type": "CAUTION", "text": f"Elevated Debt-to-Equity Ratio ({debt_to_equity:.1f}%)"})
            
    if free_cashflow is not None and free_cashflow > 0:
        long_term_score += 8
        signals.append({"type": "BULLISH", "text": f"Positive Free Cash Flow (${free_cashflow / 1e9:.2f}B)"})
        
    # 5. Analyst Consensus & Wall St Upside (Up to +15 pts)
    if recommendation_mean is not None:
        if recommendation_mean <= 1.8:
            long_term_score += 10
            signals.append({"type": "BULLISH", "text": f"Wall Street Consensus: Strong Buy ({recommendation_key})"})
        elif recommendation_mean <= 2.3:
            long_term_score += 6
            signals.append({"type": "BULLISH", "text": f"Wall Street Consensus: Buy ({recommendation_key})"})
            
    if analyst_upside_pct > 15:
        long_term_score += 8
        signals.append({"type": "BULLISH", "text": f"Analyst Consensus Target gives +{analyst_upside_pct}% upside"})
    elif analyst_upside_pct < -5:
        long_term_score -= 8
        signals.append({"type": "CAUTION", "text": f"Trading above Wall Street average target price ({analyst_upside_pct}%)"})
        
    long_term_score = round(max(5.0, min(99.0, long_term_score)), 1)
    
    # Valuation Tier
    if peg_ratio and peg_ratio < 1.2:
        val_status = "Undervalued / High Growth"
    elif forward_pe and forward_pe < 20:
        val_status = "Attractively Valued"
    elif forward_pe and forward_pe > 45:
        val_status = "Premium Valuation"
    else:
        val_status = "Fairly Valued"
        
    # Quality Grade
    if long_term_score >= 85:
        quality_grade = "AAA (Exceptional Compounder)"
    elif long_term_score >= 75:
        quality_grade = "AA (High Quality Growth)"
    elif long_term_score >= 60:
        quality_grade = "A (Solid Fundamentals)"
    elif long_term_score >= 45:
        quality_grade = "BBB (Average / Cyclical)"
    else:
        quality_grade = "C (High Risk / Speculative)"
        
    return {
        "valid": True,
        "quality_score": long_term_score,
        "quality_grade": quality_grade,
        "valuation_verdict": val_status,
        "metrics": {
            "current_price": current_price,
            "market_cap": info.get("marketCap"),
            "trailing_pe": round(trailing_pe, 2) if trailing_pe else None,
            "forward_pe": round(forward_pe, 2) if forward_pe else None,
            "peg_ratio": round(peg_ratio, 2) if peg_ratio else None,
            "price_to_book": round(price_to_book, 2) if price_to_book else None,
            "price_to_sales": round(price_to_sales, 2) if price_to_sales else None,
            "ev_to_ebitda": round(ev_to_ebitda, 2) if ev_to_ebitda else None,
            "roe": round(roe * 100, 2) if roe is not None else None,
            "profit_margin": round(profit_margins * 100, 2) if profit_margins is not None else None,
            "revenue_growth": round(revenue_growth * 100, 2) if revenue_growth is not None else None,
            "earnings_growth": round(earnings_growth * 100, 2) if earnings_growth is not None else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity is not None else None,
            "current_ratio": round(current_ratio, 2) if current_ratio is not None else None,
            "dividend_yield": round(dividend_yield * 100, 2) if dividend_yield is not None else 0.0,
            "free_cashflow": free_cashflow
        },
        "analyst_consensus": {
            "target_mean": target_mean_price,
            "target_high": target_high_price,
            "target_low": target_low_price,
            "upside_pct": analyst_upside_pct,
            "num_analysts": num_analysts,
            "rating": recommendation_key,
            "rating_mean": recommendation_mean
        },
        "signals": signals
    }

