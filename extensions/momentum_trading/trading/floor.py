import json
import os
import pandas as pd
import yfinance as yf
import logging
from typing import List, Dict, Any
from extensions.momentum_trading.trading.scanner import QullamaggieScanner, FundamentalMomentumScanner
from extensions.momentum_trading.trading.reversion import MeanReversionScanner
from extensions.momentum_trading.trading.rs import RelativeStrengthScanner
from extensions.momentum_trading.trading.regime import MarketRegimeHMM

logger = logging.getLogger(__name__)

class TradingFloor:
    """
    The Single Source of Truth for all trading strategies.
    Consolidates Momentum, Mean Reversion, and Relative Strength findings
    guided by HMM-based Market Regime detection and Dual Universes.
    """
    
    def __init__(self):
        # Determine base path for configs
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.dynamic_watchlist_path = os.path.join(self.base_dir, "configs", "dynamic_universe.json")
        self.comp_watchlist_path = os.path.join(self.base_dir, "configs", "comprehensive_universe.json")
        
        self.dynamic_watchlist = self._load_json(self.dynamic_watchlist_path)
        self.comp_watchlist = self._load_json(self.comp_watchlist_path)
        
        self.hmm = MarketRegimeHMM(n_regimes=3)

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading {path}: {e}")
        return {"symbols": [], "metadata": []}

    def get_market_regime(self) -> Dict[str, Any]:
        """Determines market state using Hidden Markov Models (HMM)."""
        logger.info("Fetching NIFTY 50 data for regime prediction...")
        nifty = yf.download("^NSEI", period="100d", interval="1d", progress=False)
        
        try:
            regime_label = self.hmm.predict_regime(nifty)
            recommendation = self.hmm.get_strategy_recommendation(regime_label)
            
            return {
                "index": "NIFTY 50",
                "price": round(nifty['Close'].iloc[-1].item(), 2),
                "regime": regime_label,
                "recommendation": recommendation,
                "is_bullish": regime_label == "BULLISH_TRENDING"
            }
        except Exception as e:
            logger.error(f"HMM Regime prediction failed: {e}. Falling back to SIDEWAYS.")
            return {
                "index": "NIFTY 50",
                "price": 0,
                "regime": "SIDEWAYS_CHOPPY",
                "recommendation": self.hmm.get_strategy_recommendation("SIDEWAYS_CHOPPY"),
                "is_bullish": False
            }

    def produce_unified_report(self) -> Dict[str, Any]:
        """Runs scanners and prioritizes based on the HMM regime."""
        regime_data = self.get_market_regime()
        regime = regime_data['regime']
        rec = regime_data['recommendation']
        
        # 1. Prepare Fundamental Scanner (Wider Universe: 2000+ NSE symbols)
        f_symbols = self.comp_watchlist.get("symbols", [])
        f_metadata = {item['symbol']: item for item in self.comp_watchlist.get('metadata', [])}
        f_scanner = FundamentalMomentumScanner(watchlist=f_symbols, universe_metadata=f_metadata)
        
        # 2. Prepare Standard Scanners (Restricted High-ADR NIFTY 500)
        s_symbols = self.dynamic_watchlist.get("symbols", [])
        m_scanner = QullamaggieScanner(watchlist=s_symbols)
        r_scanner = MeanReversionScanner(watchlist=s_symbols)
        rs_scanner = RelativeStrengthScanner(watchlist=s_symbols)
        
        momentum_setups = []
        reversion_setups = []
        fundamental_setups = []
        
        # Fundamental: Always run on wider list
        logger.info(f"Fundamental Scan: {len(f_symbols)} symbols (NSE ALL).")
        fundamental_setups = f_scanner.scan()

        # Momentum/Reversion: Run on restricted NIFTY 500 list
        if rec['primary'] == "MOMENTUM" or rec['secondary'] == "MOMENTUM":
            logger.info(f"Qullamaggie Scan: {len(s_symbols)} symbols (NIFTY 500).")
            momentum_setups = m_scanner.scan()
            
        if rec['primary'] == "MEAN_REVERSION" or rec['secondary'] == "MEAN_REVERSION":
            logger.info(f"Mean Reversion Scan: {len(s_symbols)} symbols (NIFTY 500).")
            reversion_setups = r_scanner.scan()
            
        # Relative Strength ranking remains on the dynamic list
        rs_rankings = rs_scanner.scan()
        
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "market_regime": regime_data,
            "strategies": {
                "momentum": momentum_setups,
                "reversion": reversion_setups,
                "fundamental": fundamental_setups
            },
            "rs_rankings": rs_rankings,
            "summary": {
                "total_setups": len(momentum_setups) + len(reversion_setups) + len(fundamental_setups),
                "momentum_count": len(momentum_setups),
                "reversion_count": len(reversion_setups),
                "fundamental_count": len(fundamental_setups),
                "primary_strategy": rec['primary']
            }
        }
        return report

if __name__ == "__main__":
    # Setup logging to see what's happening
    logging.basicConfig(level=logging.INFO)
    floor = TradingFloor()
    report = floor.produce_unified_report()
    # Print results summary
    print(f"\nFound {report['summary']['momentum_count']} Momentum, {report['summary']['fundamental_count']} Fundamental and {report['summary']['reversion_count']} Reversion setups.")
