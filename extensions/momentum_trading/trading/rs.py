import pandas as pd
import numpy as np
import yfinance as yf
import logging
import json
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RelativeStrengthScanner:
    """
    Architect's Hybrid Relative Strength Scanner.
    Combines Mansfield RS (PineScript) with IBD-style Percentile Ranking.
    """
    
    def __init__(self, watchlist: List[str], benchmark: str = "^NSEI", length: int = 123):
        self.watchlist = watchlist
        self.benchmark = benchmark
        self.length = length

    def get_benchmark_data(self) -> pd.Series:
        df = yf.download(self.benchmark, period="1y", interval="1d", progress=False)
        return df['Close'].dropna()

    def calculate_hybrid_metrics(self, stock_df: pd.DataFrame, benchmark_series: pd.Series) -> pd.DataFrame:
        df = stock_df.copy()
        
        # Ensure indices match
        combined = pd.concat([df['Close'], benchmark_series], axis=1, join='inner')
        combined.columns = ['Stock', 'Index']
        
        # 1. Mansfield RS (Ratio performance over 'length' days)
        stock_perf = combined['Stock'] / combined['Stock'].shift(self.length)
        index_perf = combined['Index'] / combined['Index'].shift(self.length)
        df['RS_Value'] = (stock_perf / index_perf) - 1
        
        # 2. RS Trend (SMA 50 of the RS Value as per PineScript)
        df['RS_SMA'] = df['RS_Value'].rolling(window=50).mean()
        
        # 3. RS Momentum ( ibd-style weighted returns for ranking)
        # 40% Weight to last 3 months, 20% to each of the previous three 3-month periods
        ret_3m = (combined['Stock'] / combined['Stock'].shift(63)) - 1
        ret_6m = (combined['Stock'] / combined['Stock'].shift(126)) - 1
        ret_9m = (combined['Stock'] / combined['Stock'].shift(189)) - 1
        ret_12m = (combined['Stock'] / combined['Stock'].shift(252)) - 1
        df['Weighted_Score'] = (ret_3m * 0.4) + (ret_6m * 0.2) + (ret_9m * 0.2) + (ret_12m * 0.2)
        
        return df

    def scan(self) -> List[Dict[str, Any]]:
        results = []
        benchmark_series = self.get_benchmark_data()
        if benchmark_series.empty: return []

        logger.info(f"Scanning {len(self.watchlist)} stocks for Hybrid Relative Strength...")
        
        try:
            full_df = yf.download(self.watchlist, period="2y", interval="1d", progress=False, group_by='ticker')
            
            all_data = {}
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
                    if len(df) < 252: continue
                    
                    df = self.calculate_hybrid_metrics(df, benchmark_series)
                    curr = df.iloc[-1]
                    
                    all_data[symbol] = {
                        "symbol": symbol,
                        "rs_value": float(curr['RS_Value']),
                        "rs_sma": float(curr['RS_SMA']),
                        "weighted_score": float(curr['Weighted_Score']),
                        "is_outperforming_ma": bool(curr['RS_Value'] > curr['RS_SMA']),
                        "is_rs_positive": bool(curr['RS_Value'] > 0)
                    }
                except: continue

            # Calculate RS Rating (Percentile Ranking based on Weighted Score)
            sorted_symbols = sorted(all_data.keys(), key=lambda x: all_data[x]['weighted_score'])
            total = len(sorted_symbols)
            
            for i, symbol in enumerate(sorted_symbols):
                rating = round((i + 1) / total * 100)
                data = all_data[symbol]
                
                results.append({
                    "symbol": symbol,
                    "rs_rating": rating,
                    "rs_value": round(data['rs_value'], 3),
                    "rs_trend": "BULLISH" if data['is_outperforming_ma'] else "BEARISH",
                    "status": "LEADING" if rating >= 80 and data['is_outperforming_ma'] else "LAGGING"
                })
                    
        except Exception as e:
            logger.error(f"Hybrid RS scan failed: {e}")
            
        return sorted(results, key=lambda x: x['rs_rating'], reverse=True)
