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
        
        if move_pct < 30: return {"match": False}

        tight_bars = 3 if self.interval in ["1wk", "1mo"] else 10
        last_tight = df.tail(tight_bars)
        consolidation_range = (last_tight['High'].max() - last_tight['Low'].min()) / last_tight['Low'].min() * 100
        
        is_tight = consolidation_range < (adr * 1.5)
        near_ema = (abs(curr['Close'] - curr['EMA10']) / curr['EMA10'] < 0.03) or \
                   (abs(curr['Close'] - curr['EMA20']) / curr['EMA20'] < 0.03)

        if is_tight and near_ema:
            return {
                "match": True,
                "move_pct": round(move_pct, 2),
                "details": f"Move: {move_pct:.1f}%, Range: {consolidation_range:.1f}% ({self.interval})"
            }
        return {"match": False}

    def is_episodic_pivot(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 21: return {"match": False}
        curr = df.iloc[-1]; prev = df.iloc[-2]
        gap_pct = (curr['Open'] / prev['Close'] - 1) * 100
        vol_surge = curr['Volume'] / df['VolAvg20'].iloc[-2]
        
        if (gap_pct > 8 and vol_surge > 2.5):
            return {"match": True, "details": f"Gap: {gap_pct:.1f}%, Vol: {vol_surge:.1f}x ({self.interval})"}
        return {"match": False}

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
            
            for symbol in self.watchlist:
                # Extract symbol data from multi-index or single index df
                if len(self.watchlist) > 1:
                    if symbol not in full_df.columns.levels[0]: continue
                    df = full_df[symbol].dropna()
                else:
                    df = full_df.dropna()

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
