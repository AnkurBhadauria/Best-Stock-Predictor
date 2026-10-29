# OmniStock Alpha - Multi-Horizon Stock Predictor Web Application

**OmniStock Alpha** is a full-stack, AI-driven stock discovery and prediction website designed to find the **best stocks to purchase for maximum return**, split into three distinct investment horizons:

1. **⚡ Short-Term (1-2 Weeks)**: Momentum breakout engine, fast EMA crossovers, RSI power zones, volume surge spikes, and breaking news catalysts.
2. **📈 Medium-Term (1-2 Months)**: Trend-following engine, quarterly earnings growth, 50-day moving average support, and Wall Street analyst revisions.
3. **💎 Long-Term (1-2 Years)**: Value compounding engine, high Return on Equity (ROE), low debt-to-equity, free cash flow yields, and fair value discounts.

---

## Architecture & Data Ingestion ("Information from Everywhere")

The platform integrates multi-source intelligence to synthesize a composite conviction score (0 to 100) and forecast expected returns:

- **Live Market & OHLCV Prices**: Intraday prices, daily OHLCV candlestick histories, 52-week ranges, and beta.
- **20+ Technical Indicators**:
  - RSI (14 period)
  - MACD (12, 26, 9) with Signal Line & Histogram
  - Bollinger Bands (20 period, 2 std dev) & Bandwidth Squeeze detection
  - Moving Averages (EMA 9, EMA 21, SMA 50, SMA 200)
  - Average True Range (ATR 14) for dynamic volatility and risk sizing
  - Stochastic Oscillator (%K, %D)
  - Volume Surge Ratio (Current volume vs 20-day average)
- **Fundamental & Valuation Multiples**:
  - P/E, Forward P/E, PEG Ratio, Price-to-Book, Price-to-Sales, EV/EBITDA
  - Return on Equity (ROE), Net Profit Margin, Operating Margin
  - Quarterly Revenue Growth YoY, Quarterly Earnings Growth YoY
  - Debt-to-Equity, Current Ratio, Free Cash Flow
- **Wall Street Consensus**:
  - Target Price (Mean, Median, High, Low)
  - Recommendation Mean (Strong Buy to Strong Sell) and Analyst Upside %
- **Real-Time News & Sentiment Engine**:
  - Real-time financial headlines ingested via RSS feeds covering major financial media (Bloomberg, Reuters, CNBC, Forbes, Seeking Alpha, etc.)
  - NLP financial sentiment scoring (Bullish / Neutral / Bearish polarity)
- **Actionable Trade Setup**:
  - Entry Price, Dynamic Stop-Loss, Take-Profit 1, Take-Profit 2, and Risk/Reward Ratio ($\ge 2.5:1$).

---

## Quick Start Guide

### 1. Requirements
- Python 3.10+ (Python 3.12 verified)

### 2. Run the Web App
Simply double-click `start.bat` on Windows, or run in your terminal:

```bash
python run.py
```

The app will automatically launch your browser at:
👉 **`http://127.0.0.1:8000`**

---

## REST API Endpoints

- `GET /` — Serves the interactive fintech web dashboard.
- `GET /api/recommendations?horizon=short_term` — Returns ranked leaderboard and #1 Spotlight stock for `short_term` (1-2w), `medium_term` (1-2m), or `long_term` (1-2y).
- `GET /api/stock/{ticker}` — Deep-dive multi-horizon prediction, technical indicators, fundamental ratios, real-time news, and 90-day chart data for ANY stock (e.g., `NVDA`, `AAPL`, `TSLA`, `MSFT`, `INFY`).
- `GET /api/horizons` — Metadata and weight profiles for the 3 investment horizons.
- `GET /api/universes` — Pre-configured watchlists (Tech Momentum, Growth Leaders, Blue-Chip Value, Global ADRs).
- `GET /api/health` — API health check.

