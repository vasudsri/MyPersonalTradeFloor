import pandas as pd
import numpy as np
import yfinance as yf
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class QullamaggieScanner:
    def __init__(self, watchlist: List[str] = None, interval: str = "1d"):
        self.watchlist = watchlist or ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]
        self.interval = interval

    def calculate_adr(self, df: pd.DataFrame, period: int = 20) -> float:
        daily_range = (df['High'] - df['Low']) / df['Low'] * 100
        return float(daily_range.tail(period).mean())

    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # 20-Day ADR %
        df['Daily_Range_Pct'] = 100 * (df['High'] - df['Low']) / df['Low']
        df['ADR20'] = df['Daily_Range_Pct'].rolling(20).mean()
        
        # Relative Strength (3-Month Performance)
        df['RS_3M'] = df['Close'].pct_change(63) * 100
        
        # Volume Average
        if 'Volume' in df.columns:
            df['VolAvg20'] = df['Volume'].rolling(20).mean()
        
        return df

    def is_qullamaggie_setup(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 50: return {"match": False}
        curr = df.iloc[-1]; prev = df.iloc[-2]
        
        adr_valid = curr['ADR20'] >= 4.0
        is_trending = curr['Close'] > curr['EMA50']
        is_near_ema = (abs(curr['Close'] - curr['EMA10']) / curr['EMA10'] < 0.03) or \
                      (abs(curr['Close'] - curr['EMA20']) / curr['EMA20'] < 0.03)
        is_breakout = curr['Close'] > prev['High']
        is_strong = curr['RS_3M'] > 20
        
        match = adr_valid and is_trending and is_near_ema and is_breakout and is_strong
        
        return {
            "match": match,
            "scorecard": {
                "adr_value": round(curr['ADR20'], 2),
                "rs_3m": round(curr['RS_3M'], 2),
                "is_trending": is_trending,
                "is_tight": is_near_ema,
                "is_breakout": is_breakout,
                "price": round(curr['Close'], 2)
            }
        }

    def is_episodic_pivot(self, df: pd.DataFrame) -> Dict[str, Any]:
        if len(df) < 21 or 'VolAvg20' not in df.columns: return {"match": False}
        curr = df.iloc[-1]; prev = df.iloc[-2]
        gap_pct = (curr['Open'] / prev['Close'] - 1) * 100
        vol_surge = curr['Volume'] / df['VolAvg20'].iloc[-2]
        
        scorecard = {
            "is_gap": gap_pct > 3.0,
            "is_volume": vol_surge > 2.5,
            "gap_pct": round(gap_pct, 2),
            "vol_surge": round(vol_surge, 2),
            "price": round(curr['Close'], 2)
        }
        return {"match": scorecard["is_gap"] and scorecard["is_volume"], "scorecard": scorecard}

    def scan(self) -> List[Dict[str, Any]]:
        results = []
        logger.info(f"Scanning {len(self.watchlist)} symbols for Qullamaggie/EP setups...")
        
        data = yf.download(self.watchlist, period="100d", interval=self.interval, progress=False, group_by='ticker')
        
        for symbol in self.watchlist:
            try:
                df = data[symbol] if len(self.watchlist) > 1 else data
                df = df.dropna()
                if df.empty: continue
                
                df = self.add_indicators(df)
                
                q_setup = self.is_qullamaggie_setup(df)
                if q_setup["match"]:
                    results.append({"symbol": symbol, "setup": "QULLAMAGGIE", "data": q_setup["scorecard"]})
                
                ep_setup = self.is_episodic_pivot(df)
                if ep_setup["match"]:
                    results.append({"symbol": symbol, "setup": "EPISODIC_PIVOT", "data": ep_setup["scorecard"]})
                    
            except Exception as e:
                logger.error(f"Scan failed for {symbol}: {e}")
        return results

class FundamentalMomentumScanner:
    """
    Combined Fundamental & Technical Strategy:
    1) MarketCap: 10M to 2T INR
    2) ROE: 15-20%
    3) RSI(14) > 60
    4) EMA(50) < Price
    5) EMA(200) < EMA(50)
    6) VWAP < Price
    """
    def __init__(self, watchlist: List[str], universe_metadata: Dict[str, Any]):
        self.watchlist = watchlist
        self.metadata = universe_metadata

    def calculate_vwap(self, df_1m: pd.DataFrame) -> float:
        if df_1m.empty: return 0
        v = df_1m['Volume']
        p = (df_1m['High'] + df_1m['Low'] + df_1m['Close']) / 3
        return (p * v).sum() / v.sum()

    def scan(self) -> List[Dict[str, Any]]:
        results = []
        logger.info(f"Running Fundamental Momentum Scan on {len(self.watchlist)} symbols...")
        
        for symbol in self.watchlist:
            try:
                meta = self.metadata.get(symbol, {})
                mcap = meta.get('market_cap', 0)
                roe = meta.get('roe', 0)
                
                # Fundamental Constraints
                if not (10_000_000 <= mcap <= 2_000_000_000_000): continue
                if not (0.15 <= roe <= 0.20): continue

                df = yf.download(symbol, period="300d", interval="1d", progress=False)
                if len(df) < 200: continue
                
                price = float(df['Close'].iloc[-1])
                ema50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
                ema200 = df['Close'].ewm(span=200, adjust=False).mean().iloc[-1]
                
                # RSI(14)
                delta = df['Close'].diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / ema_down
                rsi = 100 - (100 / (1 + rs.iloc[-1]))

                # VWAP Check
                df_1m = yf.download(symbol, period="1d", interval="1m", progress=False)
                vwap = self.calculate_vwap(df_1m)

                # Final Verification
                tech_match = (rsi > 60) and (price > ema50) and (ema50 > ema200) and (price > vwap)
                
                if tech_match:
                    results.append({
                        "symbol": symbol,
                        "setup": "FUND_MOMENTUM",
                        "data": {
                            "price": round(price, 2),
                            "rsi": round(rsi, 2),
                            "mcap_cr": round(mcap / 10_000_000, 2),
                            "roe_pct": round(roe * 100, 2),
                            "details": f"RSI:{round(rsi,1)} | MCAP:{round(mcap/1e7,1)}Cr | ROE:{round(roe*100,1)}%"
                        }
                    })
            except Exception as e:
                logger.error(f"Fundamental scan failed for {symbol}: {e}")
        return results
