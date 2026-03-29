import json
import os
import logging
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from extensions.momentum_trading.trading.rs import RelativeStrengthScanner

logger = logging.getLogger(__name__)

@ToolRegistry.register("nifty_rs_ranker")
class NiftyRSRankerTool(BaseTool):
    """Ranks stocks based on Hybrid Relative Strength."""
    
    tool_id = "nifty_rs_ranker"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="nifty_rs_ranker", 
            description="Calculates Hybrid Relative Strength (Mansfield + Percentile) for the NIFTY universe to identify true market leaders.", 
            parameters={"type": "object", "properties": {}}
        )
        
    def execute(self, **params) -> ToolResult:
        config_path = "extensions/momentum_trading/configs/nifty200.json"
        watchlist = []
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                watchlist = data.get("symbols", [])
        
        if not watchlist:
            watchlist = ["ADANIENT.NS", "RELIANCE.NS", "TCS.NS", "HAL.NS", "TRENT.NS"]
            
        scanner = RelativeStrengthScanner(watchlist=watchlist)
        results = scanner.scan()
        
        return ToolResult(tool_name="nifty_rs_ranker", content=json.dumps(results), success=True)
