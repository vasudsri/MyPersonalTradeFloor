import json
import os
import pandas as pd
import yfinance as yf
from typing import List, Dict, Any
from extensions.momentum_trading.trading.scanner import QullamaggieScanner
from extensions.momentum_trading.trading.reversion import MeanReversionScanner
from extensions.momentum_trading.trading.rs import RelativeStrengthScanner

class TradingFloor:
    """
    The Single Source of Truth for all trading strategies.
    Consolidates Momentum, Mean Reversion, and Relative Strength findings.
    """
    
    def __init__(self):
        self.watchlist_path = "extensions/momentum_trading/configs/nifty200.json"
        self.watchlist = self._load_watchlist()

    def _load_watchlist(self) -> List[str]:
        if os.path.exists(self.watchlist_path):
            with open(self.watchlist_path, "r") as f:
                return json.load(f).get("symbols", [])
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"]

    def get_market_regime(self) -> Dict[str, Any]:
        """Determines if the index is trending or ranging."""
        nifty = yf.download("^NSEI", period="50d", interval="1d", progress=False)
        close = nifty['Close'].iloc[-1].item()
        ema20 = nifty['Close'].ewm(span=20, adjust=False).mean().iloc[-1].item()
        ema50 = nifty['Close'].ewm(span=50, adjust=False).mean().iloc[-1].item()
        
        regime = "SIDEWAYS"
        if close > ema20 > ema50: regime = "TRENDING_UP"
        elif close < ema20 < ema50: regime = "TRENDING_DOWN"
        
        return {
            "index": "NIFTY 50",
            "price": round(close, 2),
            "regime": regime,
            "is_bullish": bool(close > ema20)
        }

    def produce_unified_report(self) -> Dict[str, Any]:
        """Runs all scanners and merges them into a single technical state."""
        regime = self.get_market_regime()
        
        print(f"--- Running Trading Floor Scanners [Regime: {regime['regime']}] ---")
        
        m_scanner = QullamaggieScanner(watchlist=self.watchlist)
        r_scanner = MeanReversionScanner(watchlist=self.watchlist)
        rs_scanner = RelativeStrengthScanner(watchlist=self.watchlist)
        
        momentum_setups = m_scanner.scan()
        reversion_setups = r_scanner.scan()
        rs_rankings = rs_scanner.scan()
        
        # Create a quick lookup for RS ratings
        rs_lookup = {item['symbol']: item for item in rs_rankings}
        
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "market_regime": regime,
            "strategies": {
                "momentum": momentum_setups,
                "reversion": reversion_setups
            },
            "rs_rankings": rs_rankings,
            "summary": {
                "total_setups": len(momentum_setups) + len(reversion_setups),
                "momentum_count": len(momentum_setups),
                "reversion_count": len(reversion_setups)
            }
        }
        return report

if __name__ == "__main__":
    floor = TradingFloor()
    report = floor.produce_unified_report()
    print(json.dumps(report, indent=2))
