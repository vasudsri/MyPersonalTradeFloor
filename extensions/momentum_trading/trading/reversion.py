import pandas as pd
import numpy as np
import yfinance as yf
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MeanReversionScanner:
    """
    Scanner for Mean Reversion setups (Oversold/Overbought).
    Focuses on RSI extremes and Bollinger Band deviations.
    """
    
    def __init__(self, watchlist: List[str], interval: str = "1d"):
        self.watchlist = watchlist
        self.interval = interval

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands (20, 2)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['STD20'] = df['Close'].rolling(window=20).std()
        df['Upper_BB'] = df['MA20'] + (2 * df['STD20'])
        df['Lower_BB'] = df['MA20'] - (2 * df['STD20'])
        
        # Z-Score (Distance from MA20)
        df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD20']
        
        return df

    def is_oversold_reversal(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 30: return {"match": False}
        curr = df.iloc[-1]
        
        # Criteria: RSI < 30 and Close near Lower BB
        scorecard = {
            "is_rsi_oversold": bool(curr['RSI'] <= 35),
            "is_below_lower_bb": bool(curr['Close'] <= curr['Lower_BB'] * 1.02),
            "is_zscore_extreme": bool(curr['Z_Score'] <= -2.0)
        }
        
        # Conviction (Baseline 5)
        conviction = 5
        if curr['RSI'] < 25: conviction += 2
        if curr['Close'] < curr['Lower_BB']: conviction += 2
        if scorecard["is_zscore_extreme"]: conviction += 1
        
        match = scorecard["is_rsi_oversold"] or scorecard["is_zscore_extreme"]
        
        return {
            "match": match,
            "setup": "OVERSOLD_REVERSION",
            "scorecard": scorecard,
            "conviction_score": min(conviction, 10),
            "details": f"RSI: {curr['RSI']:.1f}, Z-Score: {curr['Z_Score']:.1f}, BB: {curr['Lower_BB']:.1f}"
        }

    def is_overbought_reversal(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 30: return {"match": False}
        curr = df.iloc[-1]
        
        scorecard = {
            "is_rsi_overbought": bool(curr['RSI'] >= 65),
            "is_above_upper_bb": bool(curr['Close'] >= curr['Upper_BB'] * 0.98),
            "is_zscore_extreme": bool(curr['Z_Score'] >= 2.0)
        }
        
        conviction = 5
        if curr['RSI'] > 75: conviction += 2
        if curr['Close'] > curr['Upper_BB']: conviction += 2
        if scorecard["is_zscore_extreme"]: conviction += 1
        
        match = scorecard["is_rsi_overbought"] or scorecard["is_zscore_extreme"]
        
        return {
            "match": match,
            "setup": "OVERBOUGHT_REVERSION",
            "scorecard": scorecard,
            "conviction_score": min(conviction, 10),
            "details": f"RSI: {curr['RSI']:.1f}, Z-Score: {curr['Z_Score']:.1f}, BB: {curr['Upper_BB']:.1f}"
        }

    def scan(self) -> List[Dict[str, Any]]:
        results = []
        try:
            full_df = yf.download(self.watchlist, period="6mo", interval=self.interval, progress=False, group_by='ticker')
            
            for symbol in self.watchlist:
                try:
                    if len(self.watchlist) > 1:
                        if symbol not in full_df.columns.levels[0]: continue
                        df = full_df[symbol].copy()
                    else:
                        df = full_df.copy()
                    
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(-1)
                    
                    df.dropna(inplace=True)
                    if df.empty: continue
                    
                    df = self.add_indicators(df)
                    
                    oversold = self.is_oversold_reversal(df)
                    if oversold["match"]:
                        results.append({"symbol": symbol, "setup": "REVERSION_BUY", "data": oversold})
                        
                    overbought = self.is_overbought_reversal(df)
                    if overbought["match"]:
                        results.append({"symbol": symbol, "setup": "REVERSION_SELL", "data": overbought})
                        
                except Exception as e:
                    logger.warning(f"Failed scanning {symbol}: {e}")
        except Exception as e:
            logger.error(f"Bulk reversion scan failed: {e}")
            
        return results
