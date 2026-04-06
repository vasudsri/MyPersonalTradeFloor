import requests
import json
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OpenAlgoExecutor:
    """
    Execution Layer for OpenAlgo (https://github.com/marketcalls/openalgo).
    Bridges foundational HMM/Risk analysis with real broker execution.
    """
    
    def __init__(self, config_path: str = "extensions/momentum_trading/configs/openalgo.json"):
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("api_key")
        self.base_url = self.config.get("base_url", "http://localhost:5000")
        self.strategy = self.config.get("strategy_name", "Momentum_HMM")
        self.exchange = self.config.get("exchange", "NSE")
        self.is_dry_run = self.config.get("is_dry_run", True)

    def _load_config(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def place_order(self, symbol: str, side: str, quantity: int, price: float = 0, stop_loss: float = 0):
        """
        Sends a POST request to OpenAlgo's standardized order endpoint.
        """
        if quantity <= 0:
            logger.warning(f"Skipping order for {symbol}: Quantity is 0.")
            return

        # OpenAlgo API expects a specific payload format
        # Verified from restx_api/schemas.py in OpenAlgo repo
        payload = {
            "apikey": self.api_key,
            "strategy": self.strategy,
            "exchange": self.exchange,
            "symbol": symbol,
            "action": side.upper(), # BUY/SELL
            "quantity": quantity,
            "pricetype": "MARKET",
            "product": "MIS", # Defaulting to MIS for day trading
            "price": float(price),
            "trigger_price": float(stop_loss) if stop_loss > 0 else 0.0
        }

        if self.is_dry_run:
            logger.info(f"[DRY RUN - OpenAlgo] Would {side} {quantity} shares of {symbol} (Exchange: {self.exchange}) via {self.base_url}")
            logger.debug(f"Payload: {json.dumps(payload)}")
            return {"status": "success", "msg": "Dry run active"}

        try:
            url = f"{self.base_url}/api/v1/placeorder"
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            res_data = response.json()
            
            if res_data.get("status") == "success":
                logger.info(f"Order SUCCESS: {symbol} {side} Qty:{quantity}. ID: {res_data.get('order_id')}")
            else:
                logger.error(f"Order FAILED: {symbol}. Error: {res_data.get('message')}")
            
            return res_data
            
        except Exception as e:
            logger.error(f"Critical error connecting to OpenAlgo: {e}")
            return {"status": "error", "msg": str(e)}

    def cancel_all_orders(self):
        """Useful for emergency market exit or session end."""
        if self.is_dry_run:
            logger.info("[DRY RUN] Would cancel all open orders on OpenAlgo.")
            return

        payload = {"apikey": self.api_key, "strategy": self.strategy}
        try:
            # Verified endpoint from restx_api/__init__.py
            requests.post(f"{self.base_url}/api/v1/cancelallorder", json=payload)
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
