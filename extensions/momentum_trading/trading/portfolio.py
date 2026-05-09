import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Manages a virtual portfolio of trades.
    Tracks active positions until Stop Loss or Target is hit.
    Calculates P&L based on a fixed investment per position (Default: 10,000 INR).
    """
    
    def __init__(self, fixed_investment: float = 10000.0):
        self.fixed_investment = fixed_investment
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.portfolio_path = os.path.join(self.data_dir, "portfolio.json")
        self.web_portfolio_path = "OpenJarvis/frontend/public/data/portfolio.json"
        
        os.makedirs(self.data_dir, exist_ok=True)
        self.portfolio = self._load_portfolio()

    def _load_portfolio(self) -> Dict[str, Any]:
        if os.path.exists(self.portfolio_path):
            try:
                with open(self.portfolio_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
        
        return {
            "active_positions": [],
            "closed_positions": [],
            "stats": {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl_pct": 0,
                "net_pnl_currency": 0 # INR amount
            },
            "strategy_stats": {}
        }

    def _calculate_strategy_stats(self):
        strat_map = {}
        all_closed = self.portfolio["closed_positions"]
        
        for pos in all_closed:
            s_type = pos.get("setup_type", "UNKNOWN")
            if s_type not in strat_map:
                strat_map[s_type] = {"total": 0, "wins": 0, "pnl_pct": 0.0, "pnl_currency": 0.0}
            
            strat_map[s_type]["total"] += 1
            if pos["pnl_pct"] > 0:
                strat_map[s_type]["wins"] += 1
            strat_map[s_type]["pnl_pct"] += pos["pnl_pct"]
            
            # Currency PnL calculation: (PnL% / 100) * Investment
            strat_map[s_type]["pnl_currency"] += (pos["pnl_pct"] / 100.0) * self.fixed_investment
            
        final_stats = {}
        for s_type, data in strat_map.items():
            final_stats[s_type] = {
                "total_trades": data["total"],
                "win_rate": round((data["wins"] / data["total"]) * 100, 2),
                "total_pnl_pct": round(data["pnl_pct"], 2),
                "total_pnl_currency": round(data["pnl_currency"], 2)
            }
        return final_stats

    def save(self):
        try:
            # Update Active PnL Currency
            active_pnl_currency = 0
            for pos in self.portfolio["active_positions"]:
                active_pnl_currency += (pos["pnl_pct"] / 100.0) * self.fixed_investment
            
            # Closed PnL Currency
            closed_pnl_currency = sum([(p["pnl_pct"] / 100.0) * self.fixed_investment for p in self.portfolio["closed_positions"]])
            
            total = len(self.portfolio["closed_positions"])
            if total > 0:
                wins = len([p for p in self.portfolio["closed_positions"] if p["pnl_pct"] > 0])
                self.portfolio["stats"]["total_trades"] = total
                self.portfolio["stats"]["win_rate"] = round((wins / total) * 100, 2)
                self.portfolio["stats"]["total_pnl_pct"] = round(sum([p["pnl_pct"] for p in self.portfolio["closed_positions"]]), 2)
            
            self.portfolio["stats"]["net_pnl_currency"] = round(active_pnl_currency + closed_pnl_currency, 2)
            self.portfolio["stats"]["active_pnl_currency"] = round(active_pnl_currency, 2)
            self.portfolio["strategy_stats"] = self._calculate_strategy_stats()

            with open(self.portfolio_path, 'w') as f:
                json.dump(self.portfolio, f, indent=4)
            
            # Sync to web folder
            web_dir = os.path.dirname(self.web_portfolio_path)
            if os.path.exists(os.path.dirname(web_dir)):
                os.makedirs(web_dir, exist_ok=True)
                with open(self.web_portfolio_path, 'w') as f:
                    json.dump(self.portfolio, f, indent=4)
                    
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")

    def add_position(self, symbol: str, entry_price: float, stop_loss: float, target: float, setup_type: str):
        if any(p['symbol'] == symbol for p in self.portfolio["active_positions"]):
            return False
            
        new_pos = {
            "symbol": symbol,
            "entry_date": datetime.now().isoformat(),
            "entry_price": entry_price,
            "current_price": entry_price,
            "stop_loss": stop_loss,
            "target": target,
            "setup_type": setup_type,
            "investment": self.fixed_investment,
            "pnl_pct": 0.0,
            "status": "OPEN",
            "last_updated": datetime.now().isoformat()
        }
        
        self.portfolio["active_positions"].append(new_pos)
        logger.info(f"Position ADDED: {symbol} at {entry_price} (Invested: {self.fixed_investment})")
        return True

    def update_prices(self, price_map: Dict[str, float]):
        active = self.portfolio["active_positions"]
        still_active = []
        
        for pos in active:
            symbol = pos['symbol']
            if symbol in price_map:
                current_price = price_map[symbol]
                pos['current_price'] = current_price
                pos['pnl_pct'] = round(((current_price - pos['entry_price']) / pos['entry_price']) * 100, 2)
                pos['last_updated'] = datetime.now().isoformat()
                
                if current_price <= pos['stop_loss']:
                    pos['status'] = "CLOSED_SL"
                    pos['exit_price'] = pos['stop_loss']
                    pos['pnl_pct'] = round(((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100, 2)
                    pos['exit_date'] = datetime.now().isoformat()
                    self.portfolio["closed_positions"].append(pos)
                elif current_price >= pos['target']:
                    pos['status'] = "CLOSED_TARGET"
                    pos['exit_price'] = pos['target']
                    pos['pnl_pct'] = round(((pos['exit_price'] - pos['entry_price']) / pos['entry_price']) * 100, 2)
                    pos['exit_date'] = datetime.now().isoformat()
                    self.portfolio["closed_positions"].append(pos)
                else:
                    still_active.append(pos)
            else:
                still_active.append(pos)
                
        self.portfolio["active_positions"] = still_active
        self.save()
