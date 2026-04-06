import json
import os
import sys
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions.momentum_trading.trading.floor import TradingFloor
from extensions.momentum_trading.trading.risk import RiskManager
from extensions.momentum_trading.trading.portfolio import PortfolioManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MorningBattlePlan:
    """
    Synthesizes HMM Regime, Scanners, and Risk into a daily executive summary.
    Now supports Fundamental Momentum as a separate trackable strategy.
    """
    
    def __init__(self):
        self.floor = TradingFloor()
        self.risk_manager = RiskManager()
        self.portfolio_manager = PortfolioManager()
        
        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        parent_dir = os.path.dirname(self.base_dir)
        jarvis_dir = os.path.join(parent_dir, "OpenJarvis")
        
        self.output_dir = os.path.join(self.base_dir, "extensions/momentum_trading/data")
        self.web_output_dir = os.path.join(jarvis_dir, "frontend/public/data")
        self.universe_path = os.path.join(self.base_dir, "extensions/momentum_trading/configs/dynamic_universe.json")

    def _load_universe_metadata(self) -> Dict[str, Any]:
        if os.path.exists(self.universe_path):
            with open(self.universe_path, 'r') as f:
                data = json.load(f)
                return {item['symbol']: item for item in data.get('metadata', [])}
        return {}

    def generate(self):
        logger.info("Generating Morning Battle Plan...")
        
        # 1. Produce Unified Report (HMM + Scans)
        report = self.floor.produce_unified_report()
        regime_data = report['market_regime']
        summary = report['summary']
        universe_metadata = self._load_universe_metadata()
        
        # 2. Extract Top Picks
        # Gather all symbols that triggered a setup
        setup_symbols = set()
        for strat in ['momentum', 'reversion', 'fundamental']:
            for s in report['strategies'][strat]:
                setup_symbols.add(s['symbol'])
                
        # Also include top RS leaders to fill up the dashboard
        rs_rankings = sorted(report['rs_rankings'], key=lambda x: x['rs_rating'], reverse=True)
        rs_lookup = {pick['symbol']: pick for pick in rs_rankings}
        
        # Build the final list of symbols to display (all setups + top RS until 20)
        top_symbols = list(setup_symbols)
        for pick in rs_rankings:
            if len(top_symbols) >= 20: break
            if pick['symbol'] not in setup_symbols:
                top_symbols.append(pick['symbol'])
        
        # 3. Fetch LATEST PRICES
        logger.info(f"Fetching latest prices for {len(top_symbols)} stocks...")
        if len(top_symbols) > 0:
            price_data = yf.download(top_symbols, period="1d", interval="1m", progress=False)['Close']
            if isinstance(price_data, pd.DataFrame):
                price_data = price_data.iloc[-1]
            elif isinstance(price_data, pd.Series):
                price_data = {top_symbols[0]: float(price_data.iloc[-1])}
        else:
            price_data = {}
        
        # 4. Enrich Picks
        enriched_picks = []
        for symbol in top_symbols:
            last_price = float(price_data.get(symbol, universe_metadata.get(symbol, {}).get('price', 0)))
            adr_value = universe_metadata.get(symbol, {}).get('adr', 4.0)
            rs_info = rs_lookup.get(symbol, {'rs_rating': 0, 'status': 'UNKNOWN', 'rs_trend': 'UNKNOWN'})
            
            # Identify ALL Strategy Sources
            setups = []
            for strat in ['momentum', 'reversion', 'fundamental']:
                match = next((s for s in report['strategies'][strat] if s['symbol'] == symbol), None)
                if match:
                    setups.append(match['setup'])
            
            # Risk Levels
            stop_loss = self.risk_manager.calculate_adr_stop(last_price, adr_value)
            target_price = last_price + (abs(last_price - stop_loss) * 3)
            
            enriched_picks.append({
                "symbol": symbol,
                "rs_rating": rs_info['rs_rating'],
                "status": rs_info['status'],
                "trend": rs_info.get('rs_trend', 'UNKNOWN'),
                "setup_type": setups[0] if setups else "WATCHLIST",
                "all_setups": setups, # List of all matching strategies
                "is_setup": len(setups) > 0,
                "entry": round(last_price, 2),
                "stop": round(stop_loss, 2),
                "target": round(target_price, 2),
                "adr": round(adr_value, 2)
            })
            
            # Automatically add to Virtual Portfolio if it's an active setup
            if len(setups) > 0:
                self.portfolio_manager.add_position(
                    symbol=symbol,
                    entry_price=last_price,
                    stop_loss=stop_loss,
                    target=target_price,
                    setup_type=setups[0]
                )

        # Sort enriched picks: Setups first, then by RS rating
        enriched_picks = sorted(enriched_picks, key=lambda x: (x['is_setup'], x['rs_rating']), reverse=True)

        # Update Summary
        summary['universe_size'] = len(self.floor.dynamic_watchlist.get('symbols', [])) + len(self.floor.comp_watchlist.get('symbols', []))

        # 5. Save JSON
        battle_plan = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "market_regime": regime_data,
            "scan_summary": summary,
            "scanner_data": enriched_picks
        }
        
        # Clean NaN
        def clean_json(obj):
            if isinstance(obj, dict): return {k: clean_json(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [clean_json(v) for v in obj]
            elif isinstance(obj, float) and (obj != obj or obj == float('inf') or obj == float('-inf')): return 0
            return obj

        battle_plan = clean_json(battle_plan)
        
        for d in [self.output_dir, self.web_output_dir]:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "battle_plan.json"), "w") as f:
                json.dump(battle_plan, f, indent=4)
            
        self.portfolio_manager.save()
        logger.info(f"Battle plan synced successfully.")
        return battle_plan

if __name__ == "__main__":
    plan = MorningBattlePlan()
    plan.generate()
