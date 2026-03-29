import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QullamaggieScanner:
    """
    Optimized Momentum Scanner.
    Uses bulk downloads to avoid timeouts.
    """
    
    CONFIG_PATH = "extensions/momentum_trading/configs/nifty200.json"
    
    FALLBACK_WATCHLIST = [
        "ADANIENT.NS", "CHOLAFIN.NS", "DLF.NS", "RECLTD.NS", "CANBK.NS",
        "JINDALSTEL.NS", "CGPOWER.NS", "BEL.NS", "JSWSTEEL.NS", "BANKBARODA.NS"
    ]

    def __init__(self, watchlist: Optional[List[str]] = None, interval: str = "1d"):
        self.interval = interval
        self.watchlist = watchlist or self._load_watchlist()
        logger.info(f"Scanner initialized for timeframe: {self.interval} ({len(self.watchlist)} symbols)")

    def _load_watchlist(self) -> List[str]:
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    symbols = data.get("symbols", [])
                    if symbols: return symbols
            except Exception as e:
                logger.error(f"Error reading {self.CONFIG_PATH}: {e}")
        return self.FALLBACK_WATCHLIST

    def calculate_adr(self, df: pd.DataFrame, period: int = 20) -> float:
        if len(df) < period: return 0.0
        daily_range = (df['High'] - df['Low']) / df['Low'] * 100
        return float(daily_range.tail(period).mean())

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['VolAvg20'] = df['Volume'].rolling(window=20).mean()
        
        # Stochastic (9,3,3) - Short term pullback
        low_min = df['Low'].rolling(window=9).min()
        high_max = df['High'].rolling(window=9).max()
        df['Stoch_K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Stochastic (55,5,3) - Long term trend health
        low_min_long = df['Low'].rolling(window=55).min()
        high_max_long = df['High'].rolling(window=55).max()
        df['Stoch_K_Long'] = 100 * (df['Close'] - low_min_long) / (high_max_long - low_min_long)
        df['Stoch_D_Long'] = df['Stoch_K_Long'].rolling(window=5).mean()
        
        return df

    def is_high_tight_flag(self, df: pd.DataFrame) -> Dict[str, Any]:
        lookback = 12 if self.interval == "1wk" else (4 if self.interval == "1mo" else 60)
        if len(df) < lookback: return {"match": False}

        curr = df.iloc[-1]
        adr = self.calculate_adr(df)
        
        last_period = df.tail(lookback)
        min_low = last_period['Low'].min()
        max_high = last_period['High'].max()
        move_pct = (max_high - min_low) / min_low * 100
        
        tight_bars = 3 if self.interval in ["1wk", "1mo"] else 10
        last_tight = df.tail(tight_bars)
        consolidation_range = (last_tight['High'].max() - last_tight['Low'].min()) / last_tight['Low'].min() * 100
        
        # Deterministic Scorecard
        scorecard = {
            "is_adr_valid": bool(adr >= 4.0),
            "is_move_valid": bool(move_pct >= 30),
            "is_tight": bool(consolidation_range < (adr * 1.5)),
            "is_near_ema10": bool(abs(curr['Close'] - curr['EMA10']) / curr['EMA10'] < 0.03),
            "is_near_ema20": bool(abs(curr['Close'] - curr['EMA20']) / curr['EMA20'] < 0.03),
        }
        
        match = scorecard["is_adr_valid"] and scorecard["is_move_valid"] and scorecard["is_tight"] and (scorecard["is_near_ema10"] or scorecard["is_near_ema20"])

        return {
            "match": match,
            "move_pct": round(move_pct, 2),
            "adr": round(adr, 2),
            "scorecard": scorecard,
            "details": f"Move: {move_pct:.1f}%, ADR: {adr:.1f}%, Range: {consolidation_range:.1f}% ({self.interval})"
        }

    def is_episodic_pivot(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 21: return {"match": False}
        curr = df.iloc[-1]; prev = df.iloc[-2]
        gap_pct = (curr['Open'] / prev['Close'] - 1) * 100
        vol_surge = curr['Volume'] / df['VolAvg20'].iloc[-2]
        
        scorecard = {
            "is_gap_valid": bool(gap_pct > 8),
            "is_vol_surge_valid": bool(vol_surge > 2.5)
        }
        
        match = scorecard["is_gap_valid"] and scorecard["is_vol_surge_valid"]

        return {
            "match": match, 
            "scorecard": scorecard,
            "details": f"Gap: {gap_pct:.1f}%, Vol: {vol_surge:.1f}x ({self.interval})"
        }

    def scan(self) -> List[Dict[str, Any]]:
        """
        Runs the scan using BULK download for speed.
        """
        results = []
        logger.info(f"Downloading data for {len(self.watchlist)} symbols in bulk...")
        
        period = "2y" if self.interval in ["1wk", "1mo"] else "1y"
        
        try:
            # Bulk download
            full_df = yf.download(self.watchlist, period=period, interval=self.interval, progress=False, group_by='ticker')
            
            # If only one symbol was requested, yfinance might not return a multi-index level 0
            # Let's ensure we handle both cases correctly
            for symbol in self.watchlist:
                try:
                    if len(self.watchlist) > 1:
                        if symbol not in full_df.columns.levels[0]: continue
                        df = full_df[symbol].copy()
                    else:
                        # For single symbol, yfinance might not have ticker level
                        df = full_df.copy()
                    
                    # If columns are still multi-indexed (e.g. from single-ticker download with group_by)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)

                    df.dropna(inplace=True)
                except Exception as extract_err:
                    logger.warning(f"Failed to extract data for {symbol}: {extract_err}")
                    continue

                if df.empty: continue
                
                df = self.add_indicators(df)
                
                htf = self.is_high_tight_flag(df)
                if htf["match"]:
                    results.append({"symbol": symbol, "setup": "HTF", "data": htf})
                    
                ep = self.is_episodic_pivot(df)
                if ep["match"]:
                    results.append({"symbol": symbol, "setup": "EP", "data": ep})
                    
        except Exception as e:
            logger.error(f"Bulk scan failed: {e}")
            
        logger.info(f"Scan complete. Found {len(results)} setups.")
        return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", choices=["1d", "1wk", "1mo"], default="1d")
    args = parser.parse_args()
    
    scanner = QullamaggieScanner(interval=args.interval)
    found = scanner.scan()
    for item in found:
        print(f"[{item['setup']}] {item['symbol']}: {item['data']['details']}")
