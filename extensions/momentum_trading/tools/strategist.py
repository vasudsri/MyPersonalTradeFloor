import json
import logging
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from extensions.momentum_trading.trading.floor import TradingFloor

logger = logging.getLogger(__name__)

@ToolRegistry.register("get_unified_trading_report")
class UnifiedReportTool(BaseTool):
    """Generates a combined technical report from all active strategies."""
    
    tool_id = "get_unified_trading_report"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_unified_trading_report", 
            description="Executes all strategy scanners (Momentum, Mean Reversion) and returns a unified JSON technical report including market regime.", 
            parameters={"type": "object", "properties": {}}
        )
        
    def execute(self, **params) -> ToolResult:
        try:
            floor = TradingFloor()
            report = floor.produce_unified_report()
            return ToolResult(tool_name="get_unified_trading_report", content=json.dumps(report), success=True)
        except Exception as e:
            logger.error(f"Unified report failed: {e}")
            return ToolResult(tool_name="get_unified_trading_report", content=f"Error generating report: {str(e)}", success=False)

@ToolRegistry.register("get_execution_advice")
class ExecutionAdvisorTool(BaseTool):
    """Provides specific Qullamaggie/Reversion execution orders."""
    
    tool_id = "get_execution_advice"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_execution_advice", 
            description="Returns detailed entry, stop-loss, and exit instructions for a specific setup type.", 
            parameters={
                "type": "object", 
                "properties": {
                    "strategy": {"type": "string", "enum": ["MOMENTUM", "REVERSION"]},
                    "setup": {"type": "string"}
                },
                "required": ["strategy", "setup"]
            }
        )
        
    def execute(self, **params) -> ToolResult:
        strategy = params["strategy"]
        setup = params["setup"]
        
        advice = {}
        
        if strategy == "MOMENTUM":
            advice = {
                "entry_type": "BREAKOUT",
                "entry_trigger": "Execute immediately on breakout of Yesterday's High or 5-min Opening Range High. Do not wait for retest.",
                "initial_stop": "Low of the breakout candle or Day's Low.",
                "position_sizing": "Aggressive; 1% risk on capital.",
                "exit_strategy": "Sell 1/2 at 3-5 days. Trail remainder with 10 EMA."
            }
        else: # REVERSION
            advice = {
                "entry_type": "RETEST / RECLAIM",
                "entry_trigger": "Wait for 'W' pattern or price to reclaim the Lower Bollinger Band. Execute on the first higher-low retest.",
                "initial_stop": "Strictly below the recent extreme swing low.",
                "position_sizing": "Tactical; smaller size as you are fighting the trend.",
                "exit_strategy": "Exit fully at the 20 EMA (The Mean). Do not linger."
            }
            
        return ToolResult(tool_name="get_execution_advice", content=json.dumps(advice), success=True)
