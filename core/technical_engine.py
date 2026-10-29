"""
Technical Analysis Engine.
Calculates indicators (RSI, MACD, Bollinger Bands, ATR, EMAs, Stochastics, Volume surge)
and produces short-term and medium-term technical momentum scores.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Compute MACD, Signal, and Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Compute Bollinger Upper, Lower, Middle bands and Bandwidth."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    bandwidth = ((upper - lower) / middle.replace(0, np.nan)) * 100
    return upper, middle, lower, bandwidth.fillna(0)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range (ATR)."""
    high = df['High']
    low = df['Low']
    close_prev = df['Close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return atr.bfill().fillna(0)


def compute_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Compute Stochastic %K and %D."""
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    denom = (high_max - low_min).replace(0, np.nan)
    stoch_k = 100 * ((df['Close'] - low_min) / denom)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    return stoch_k.fillna(50), stoch_d.fillna(50)


def analyze_technicals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform full technical analysis on a DataFrame with OHLCV data.
    Returns technical indicators, signals, short-term and medium-term scores.
    """
    if df is None or len(df) < 30:
        return {
            "valid": False,
            "error": "Insufficient historical data for technical analysis (need at least 30 candles)"
        }
    
    # Ensure correct columns and clean data
    df = df.copy()
    close = df['Close']
    current_price = float(close.iloc[-1])
    
    # EMAs & SMAs
    ema_9 = close.ewm(span=9, adjust=False).mean()
    ema_21 = close.ewm(span=21, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean() if len(df) >= 200 else close.rolling(window=len(df)).mean()
    
    # RSI
    rsi_series = compute_rsi(close, 14)
    current_rsi = float(rsi_series.iloc[-1])
    prev_rsi = float(rsi_series.iloc[-2]) if len(rsi_series) > 1 else current_rsi
    
    # MACD
    macd, macd_signal, macd_hist = compute_macd(close)
    current_macd = float(macd.iloc[-1])
    current_signal = float(macd_signal.iloc[-1])
    current_hist = float(macd_hist.iloc[-1])
    prev_hist = float(macd_hist.iloc[-2]) if len(macd_hist) > 1 else current_hist
    
    # Bollinger Bands
    bb_upper, bb_mid, bb_lower, bb_width = compute_bollinger_bands(close, 20, 2.0)
    current_bb_upper = float(bb_upper.iloc[-1])
    current_bb_lower = float(bb_lower.iloc[-1])
    current_bb_width = float(bb_width.iloc[-1])
    bb_pct_b = float((current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)) if (current_bb_upper - current_bb_lower) > 0 else 0.5
    
    # ATR & Volatility
    atr_series = compute_atr(df, 14)
    current_atr = float(atr_series.iloc[-1]) if not atr_series.empty else current_price * 0.02
    atr_pct = (current_atr / current_price) * 100 if current_price > 0 else 2.0
    
    # Stochastic
    stoch_k, stoch_d = compute_stochastic(df, 14, 3)
    current_k = float(stoch_k.iloc[-1])
    current_d = float(stoch_d.iloc[-1])
    
    # Volume Dynamics
    vol = df['Volume']
    current_vol = float(vol.iloc[-1])
    vol_sma_20 = float(vol.rolling(window=20).mean().iloc[-1]) if len(vol) >= 20 else current_vol
    vol_surge_ratio = (current_vol / vol_sma_20) if vol_sma_20 > 0 else 1.0
    
    # Momentum Returns
    ret_5d = float(((current_price / close.iloc[-5]) - 1) * 100) if len(df) >= 5 else 0.0
    ret_10d = float(((current_price / close.iloc[-10]) - 1) * 100) if len(df) >= 10 else 0.0
    ret_20d = float(((current_price / close.iloc[-20]) - 1) * 100) if len(df) >= 20 else 0.0
    ret_60d = float(((current_price / close.iloc[-60]) - 1) * 100) if len(df) >= 60 else 0.0
    
    # Signals Generation
    signals = []
    
    # Short-Term Signals
    if current_rsi < 35 and current_rsi > prev_rsi:
        signals.append({"type": "BULLISH", "text": "RSI Oversold Reversal (Bounce Opportunity)"})
    elif 50 <= current_rsi <= 68 and current_rsi > prev_rsi:
        signals.append({"type": "BULLISH", "text": "Strong Bullish Momentum (RSI in Power Zone)"})
    elif current_rsi > 75:
        signals.append({"type": "CAUTION", "text": "RSI Overbought (>75) - Potential near-term pullback"})
        
    if current_hist > 0 and current_hist > prev_hist:
        signals.append({"type": "BULLISH", "text": "MACD Histogram Expanding Bullish"})
    elif current_macd > current_signal and macd.iloc[-2] <= macd_signal.iloc[-2]:
        signals.append({"type": "BULLISH", "text": "Fresh MACD Bullish Crossover"})
        
    if vol_surge_ratio >= 1.5:
        signals.append({"type": "BULLISH", "text": f"High Volume Surge ({vol_surge_ratio:.1f}x 20-day avg)"})
        
    if current_price > float(ema_9.iloc[-1]) > float(ema_21.iloc[-1]):
        signals.append({"type": "BULLISH", "text": "Stacked Fast Moving Averages (Price > EMA9 > EMA21)"})
        
    # Medium-Term Trend Signals
    cur_sma50 = float(sma_50.iloc[-1])
    cur_sma200 = float(sma_200.iloc[-1])
    if current_price > cur_sma50:
        signals.append({"type": "BULLISH", "text": "Trading above 50-day SMA (Stage 2 Uptrend)"})
    if cur_sma50 > cur_sma200:
        signals.append({"type": "BULLISH", "text": "Golden Cross Alignment (50 SMA > 200 SMA)"})
        
    # Short-Term Score Calculation (0 - 100)
    st_score = 50.0  # baseline
    
    # RSI factor (-15 to +20)
    if 50 <= current_rsi <= 68:
        st_score += 18
    elif 40 <= current_rsi < 50:
        st_score += 8
    elif current_rsi < 35 and current_rsi > prev_rsi:
        st_score += 15
    elif current_rsi > 75:
        st_score -= 10
    elif current_rsi < 30:
        st_score -= 5
        
    # MACD factor (-10 to +20)
    if current_macd > current_signal:
        st_score += 10
        if current_hist > prev_hist:
            st_score += 10
    else:
        st_score -= 10
        
    # Volume Factor (0 to +20)
    if vol_surge_ratio >= 2.0:
        st_score += 20
    elif vol_surge_ratio >= 1.4:
        st_score += 12
    elif vol_surge_ratio >= 1.1:
        st_score += 6
    elif vol_surge_ratio < 0.7:
        st_score -= 8
        
    # Price vs Fast EMAs (-15 to +15)
    if current_price > float(ema_9.iloc[-1]) > float(ema_21.iloc[-1]):
        st_score += 15
    elif current_price < float(ema_9.iloc[-1]) < float(ema_21.iloc[-1]):
        st_score -= 15
        
    # Bollinger %B Breakout
    if 0.7 <= bb_pct_b <= 1.05:
        st_score += 10
        
    # Clamp Short-Term Score
    short_term_score = round(max(5.0, min(98.0, st_score)), 1)
    
    # Medium-Term Score Calculation (0 - 100)
    mt_score = 50.0
    if current_price > cur_sma50:
        mt_score += 18
    else:
        mt_score -= 15
        
    if cur_sma50 > cur_sma200:
        mt_score += 16
    else:
        mt_score -= 12
        
    if ret_60d > 10:
        mt_score += 15
    elif ret_60d > 0:
        mt_score += 8
    else:
        mt_score -= 10
        
    if current_macd > 0:
        mt_score += 10
        
    medium_term_score = round(max(5.0, min(98.0, mt_score)), 1)
    
    # Dynamic Trade Setup (Risk Management)
    # Stop-Loss: 1.5 * ATR below current price (or recent 5-day low)
    recent_5d_low = float(df['Low'].iloc[-5:].min())
    stop_loss = round(max(recent_5d_low * 0.98, current_price - (1.5 * current_atr)), 2)
    risk_per_share = max(0.01, current_price - stop_loss)
    
    # Targets for 1-2 Weeks (2.0R and 3.5R reward)
    take_profit_1 = round(current_price + (2.0 * risk_per_share), 2)
    take_profit_2 = round(current_price + (3.5 * risk_per_share), 2)
    risk_reward_ratio = round((take_profit_1 - current_price) / risk_per_share, 2)
    
    return {
        "valid": True,
        "current_price": current_price,
        "rsi": round(current_rsi, 2),
        "macd": round(current_macd, 3),
        "macd_signal": round(current_signal, 3),
        "macd_hist": round(current_hist, 3),
        "bb_upper": round(current_bb_upper, 2),
        "bb_mid": round(bb_mid.iloc[-1], 2),
        "bb_lower": round(current_bb_lower, 2),
        "bb_bandwidth": round(current_bb_width, 2),
        "atr": round(current_atr, 2),
        "atr_pct": round(atr_pct, 2),
        "stoch_k": round(current_k, 2),
        "stoch_d": round(current_d, 2),
        "volume_surge_ratio": round(vol_surge_ratio, 2),
        "ema_9": round(float(ema_9.iloc[-1]), 2),
        "ema_21": round(float(ema_21.iloc[-1]), 2),
        "sma_50": round(cur_sma50, 2),
        "sma_200": round(cur_sma200, 2),
        "returns": {
            "5d": round(ret_5d, 2),
            "10d": round(ret_10d, 2),
            "20d": round(ret_20d, 2),
            "60d": round(ret_60d, 2)
        },
        "trade_setup": {
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_reward_ratio": risk_reward_ratio,
            "risk_pct": round(((current_price - stop_loss) / current_price) * 100, 2),
            "target_pct_tp1": round(((take_profit_1 - current_price) / current_price) * 100, 2),
            "target_pct_tp2": round(((take_profit_2 - current_price) / current_price) * 100, 2)
        },
        "short_term_score": short_term_score,
        "medium_term_score": medium_term_score,
        "signals": signals
    }

