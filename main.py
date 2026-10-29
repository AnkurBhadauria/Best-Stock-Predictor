"""
FastAPI Server for Stock Predictor Web Application.
Serves REST APIs for Short-Term, Medium-Term, and Long-Term Stock Predictions
and delivers the modern fintech UI.
"""

import os
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.config import HORIZONS, PRESET_UNIVERSES, SCREENING_UNIVERSE
from core.data_fetcher import fetch_stock_data
from core.predictor_engine import evaluate_stock, get_ranked_recommendations

app = FastAPI(
    title="OmniStock Alpha - Multi-Horizon Stock Predictor",
    description="Advanced multi-source AI stock screening and prediction engine for Short-Term (1-2w), Medium-Term (1-2m), and Long-Term (1-2y) returns.",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serves the main web application UI."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "OmniStock Alpha API is live. Web UI coming up."}


@app.get("/api/horizons")
async def get_horizons_meta():
    """Returns available investment horizons and configuration."""
    return HORIZONS


@app.get("/api/universes")
async def get_universes():
    """Returns preset stock universe categories."""
    return {
        "presets": PRESET_UNIVERSES,
        "master_screen_count": len(SCREENING_UNIVERSE)
    }


@app.get("/api/recommendations")
async def get_recommendations(
    horizon: str = Query("short_term", description="short_term (1-2w), medium_term (1-2m), or long_term (1-2y)"),
    category: Optional[str] = Query(None, description="Preset universe filter (e.g. tech_momentum, growth_leaders, blue_chip_value)")
):
    """
    Ranks the best stocks to purchase for the selected investment timeframe.
    Splits predictions by Short-Term (1-2 Weeks), Medium-Term (1-2 Months), and Long-Term (1-2 Years).
    """
    if horizon not in HORIZONS:
        raise HTTPException(status_code=400, detail=f"Invalid horizon. Choose from: {list(HORIZONS.keys())}")
        
    custom_list = None
    if category and category in PRESET_UNIVERSES:
        custom_list = PRESET_UNIVERSES[category]
        
    results = get_ranked_recommendations(horizon=horizon, custom_universe=custom_list)
    return results


@app.get("/api/stock/{ticker}")
async def get_stock_analysis(ticker: str):
    """
    Deep-dive multi-horizon prediction & factor breakdown for ANY stock ticker.
    Returns Short-Term (1-2w), Medium-Term (1-2m), Long-Term (1-2y) targets,
    technicals (RSI, MACD, BB, ATR), fundamentals (P/E, PEG, ROE), news sentiment & trade setups.
    """
    symbol = ticker.strip().upper()
    bundle = fetch_stock_data(symbol, period="1y")
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Stock ticker '{symbol}' not found or insufficient market data.")
        
    evaluation = evaluate_stock(bundle)
    if not evaluation:
        raise HTTPException(status_code=500, detail=f"Could not calculate prediction metrics for '{symbol}'.")
        
    return evaluation


@app.get("/api/health")
async def health_check():
    """System health check endpoint."""
    return {"status": "healthy", "service": "OmniStock Predictor API", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

