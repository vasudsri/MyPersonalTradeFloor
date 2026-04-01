import pandas as pd
import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Mathematical Risk Engine using Fractional Kelly Criterion.
    Optimizes position size based on historical strategy edge and user capital.
    """
    
    def __init__(self):
        self.config_path = "extensions/momentum_trading/configs/portfolio.json"
        self.log_dir = "extensions/momentum_trading/data"
        self._load_config()

    def _load_config(self):
        """Loads user-specific capital and risk settings."""
        defaults = {
            "total_capital": 1000000.0,
            "max_risk_per_trade_pct": 5.0,
            "kelly_fraction": 0.25
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.total_capital = config.get("total_capital", defaults["total_capital"])
                    self.max_risk_per_trade = config.get("max_risk_per_trade_pct", defaults["max_risk_per_trade_pct"]) / 100.0
                    self.kelly_fraction = config.get("kelly_fraction", defaults["kelly_fraction"])
                    return
            except Exception as e:
                logger.error(f"Error reading portfolio config: {e}")
        
        self.total_capital = defaults["total_capital"]
        self.max_risk_per_trade = defaults["max_risk_per_trade_pct"] / 100.0
        self.kelly_fraction = defaults["kelly_fraction"]

    def get_strategy_metrics(self, strategy: str) -> Dict[str, float]:
        """
        Parses historical logs to find Win Rate (p) and Win/Loss Ratio (b).
        """
        log_file = "orb_stocks_backtest_log.csv" if strategy == "MOMENTUM" else "index_backtest_log.csv"
        path = os.path.join(self.log_dir, log_file)
        
        # Default/Fallback Metrics (Conservative)
        defaults = {"win_rate": 0.40, "win_loss_ratio": 2.0}
        
        if not os.path.exists(path):
            return defaults
            
        try:
            df = pd.read_csv(path)
            if df.empty: return defaults
            
            pnl_col = 'PnL_Pct'
            wins = df[df[pnl_col] > 0]
            losses = df[df[pnl_col] <= 0]
            
            win_rate = len(wins) / len(df)
            avg_win = wins[pnl_col].mean()
            avg_loss = abs(losses[pnl_col].mean())
            
            win_loss_ratio = avg_win / avg_loss if avg_loss != 0 else 2.0
            
            return {
                "win_rate": round(win_rate, 2),
                "win_loss_ratio": round(win_loss_ratio, 2)
            }
        except Exception as e:
            logger.error(f"Error parsing risk metrics for {strategy}: {e}")
            return defaults

    def calculate_kelly_size(self, strategy: str) -> float:
        """
        Calculates the Kelly Fraction using the user-defined safety fraction.
        """
        metrics = self.get_strategy_metrics(strategy)
        p = metrics["win_rate"]
        b = metrics["win_loss_ratio"]
        
        # Full Kelly Formula
        f_star = (p * (b + 1) - 1) / b
        
        # Apply Fractional Kelly and Portfolio Cap
        safe_size = max(0, f_star * self.kelly_fraction)
        final_size = min(safe_size, self.max_risk_per_trade)
        
        return round(final_size, 4)

    def get_position_details(self, symbol: str, strategy: str, entry_price: float, stop_loss: float) -> Dict[str, Any]:
        """
        Calculates the exact quantity to buy based on Kelly % and technical SL.
        """
        kelly_fraction = self.calculate_kelly_size(strategy)
        
        # Risk amount in Currency (e.g. INR)
        risk_amount = self.total_capital * kelly_fraction
        
        # Risk per share
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            quantity = 0
        else:
            quantity = int(risk_amount / risk_per_share)
            
        return {
            "symbol": symbol,
            "capital_allocated_pct": round(kelly_fraction * 100, 2),
            "risk_amount": round(risk_amount, 2),
            "quantity": quantity,
            "p": self.get_strategy_metrics(strategy)["win_rate"],
            "b": self.get_strategy_metrics(strategy)["win_loss_ratio"]
        }
