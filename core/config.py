"""
Configuration and constants for Stock Predictor Engine.
Defines universes, horizon weights, and indicator parameters.
"""

from typing import List, Dict, Any

# Pre-defined liquid universe across sectors for screening
PRESET_UNIVERSES = {
    "tech_momentum": [
        "NVDA", "TSLA", "AMD", "PLTR", "ARM", "SMCI", "META", "AMZN",
        "GOOGL", "MSFT", "AAPL", "AVGO", "QCOM", "COIN", "CRWD", "NOW"
    ],
    "growth_leaders": [
        "AMZN", "GOOGL", "META", "MSFT", "NVDA", "AAPL", "NFLX", "UBER",
        "SHOP", "PANW", "SNOW", "MELI", "CRM", "ADBE", "ISRG", "TSM"
    ],
    "blue_chip_value": [
        "BRK-B", "JPM", "V", "LLY", "COST", "WMT", "PG", "UNH",
        "HD", "MA", "JNJ", "ABBV", "XOM", "CVX", "MRK", "KO"
    ],
    "global_tech_adr": [
        "TSM", "ASML", "BABA", "INFY", "SAP", "SE", "SONY"
    ]
}

# Master screen list combining top liquid leaders
SCREENING_UNIVERSE = list(dict.fromkeys(
    PRESET_UNIVERSES["tech_momentum"] +
    PRESET_UNIVERSES["growth_leaders"] +
    PRESET_UNIVERSES["blue_chip_value"] +
    PRESET_UNIVERSES["global_tech_adr"]
))

# Investment Horizons Definition
HORIZONS = {
    "short_term": {
        "id": "short_term",
        "label": "Short-Term (1-2 Weeks)",
        "duration_days": 14,
        "trading_days": 10,
        "description": "Exploits momentum breakouts, RSI inflections, volume surges, and immediate news catalysts.",
        "weights": {
            "technical_momentum": 0.40,
            "volume_flow": 0.25,
            "news_sentiment": 0.20,
            "volatility_reward": 0.15
        },
        "target_return_range": (3.0, 12.0),  # expected return %
        "risk_profile": "High / Dynamic Stop Loss"
    },
    "medium_term": {
        "id": "medium_term",
        "label": "Medium-Term (1-2 Months)",
        "duration_days": 60,
        "trading_days": 42,
        "description": "Captures quarterly earnings acceleration, 50-day moving average trend continuations, and analyst upgrades.",
        "weights": {
            "trend_continuation": 0.35,
            "earnings_growth": 0.25,
            "analyst_upside": 0.25,
            "relative_strength": 0.15
        },
        "target_return_range": (8.0, 25.0),
        "risk_profile": "Moderate / Trailing Stop"
    },
    "long_term": {
        "id": "long_term",
        "label": "Long-Term (1-2 Years)",
        "duration_days": 730,
        "trading_days": 504,
        "description": "Maximizes multi-year compounding through high ROE, pristine balance sheets, valuation discounts, and competitive moats.",
        "weights": {
            "fundamental_quality": 0.40,
            "valuation_fair_value": 0.30,
            "wall_st_consensus": 0.20,
            "balance_sheet_safety": 0.10
        },
        "target_return_range": (20.0, 75.0),
        "risk_profile": "Low to Moderate / Value Compounding"
    }
}

# Cache settings (seconds)
CACHE_TTL_PRICE = 900       # 15 minutes
CACHE_TTL_FUNDAMENTAL = 86400  # 24 hours
CACHE_TTL_SCREENER = 1800   # 30 minutes

