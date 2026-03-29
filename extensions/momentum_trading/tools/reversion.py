import json
import os
import logging
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from extensions.momentum_trading.trading.reversion import MeanReversionScanner

logger = logging.getLogger(__name__)

@ToolRegistry.register("nifty_reversion_scan")
class NiftyReversionScanTool(BaseTool):
    """Scans for Oversold/Overbought mean reversion setups."""
    
    tool_id = "nifty_reversion_scan"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="nifty_reversion_scan", 
            description="Scans the NIFTY universe for stocks at technical extremes (RSI/Bollinger Bands) likely to revert to the mean.", 
            parameters={"type": "object", "properties": {}}
        )
        
    def execute(self, **params) -> ToolResult:
        # Load watchlist from config
        config_path = "extensions/momentum_trading/configs/nifty200.json"
        watchlist = []
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                watchlist = data.get("symbols", [])
        
        if not watchlist:
            watchlist = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
            
        scanner = MeanReversionScanner(watchlist=watchlist)
        results = scanner.scan()
        
        return ToolResult(tool_name="nifty_reversion_scan", content=json.dumps(results), success=True)
