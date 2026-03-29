import json
import logging
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from extensions.momentum_trading.trading.floor import TradingFloor

logger = logging.getLogger(__name__)

@ToolRegistry.register("generate_battle_plan_draft")
class BattlePlanDraftTool(BaseTool):
    """Deterministic tool to generate a structured JSON battle plan draft."""
    
    tool_id = "generate_battle_plan_draft"
    
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="generate_battle_plan_draft", 
            description="Automatically generates a structured JSON Battle Plan draft by merging scans and applying regime-based logic. Use this as your baseline.", 
            parameters={"type": "object", "properties": {}}
        )
        
    def execute(self, **params) -> ToolResult:
        try:
            floor = TradingFloor()
            report = floor.produce_unified_report()
            
            regime = report["market_regime"]["regime"]
            is_bullish = report["market_regime"]["is_bullish"]
            
            # Create a quick lookup for RS ratings
            rs_lookup = {item['symbol']: item for item in report.get("rs_rankings", [])}
            
            # 1. Strategy Priority
            priority = "BALANCED"
            if regime == "TRENDING_UP": priority = "MOMENTUM"
            elif regime == "TRENDING_DOWN": priority = "REVERSION"
            
            # 2. Merge and Rank Setups
            all_picks = []
            
            # Execution Logic Helper
            def get_advice(strat):
                if strat == "MOMENTUM":
                    return {
                        "entry": "BREAKOUT of Yesterday's High + 1 tick. Do not wait for retest.",
                        "stop_loss": "Low of the Breakout Candle.",
                        "exit": "Sell 50% at +5%, trail rest with 10 EMA."
                    }
                else:
                    return {
                        "entry": "RETEST of technical low. Wait for price reclaim of Lower BB.",
                        "stop_loss": "Strictly below recent swing low.",
                        "exit": "Exit fully at the 20 EMA (The Mean)."
                    }

            # Extract Momentum
            for s in report["strategies"]["momentum"]:
                symbol = s["symbol"]
                conviction = s["data"]["conviction_score"]
                rs_data = rs_lookup.get(symbol, {"rs_rating": 50, "rs_trend": "UNKNOWN"})
                
                if rs_data["rs_rating"] >= 90: conviction += 1
                if rs_data["rs_trend"] == "BULLISH": conviction += 1
                if rs_data["rs_rating"] < 70: conviction -= 2
                if regime == "TRENDING_DOWN": conviction -= 2
                
                all_picks.append({
                    "symbol": symbol,
                    "strategy": "MOMENTUM",
                    "conviction": max(1, min(10, conviction)),
                    "setup": s["setup"],
                    "action": "BUY",
                    "execution": get_advice("MOMENTUM"),
                    "logic": f"RS: {rs_data['rs_rating']} ({rs_data['rs_trend']}). {s['data']['details']}"
                })
                
            # Extract Reversion
            for s in report["strategies"]["reversion"]:
                symbol = s["symbol"]
                conviction = s["data"]["conviction_score"]
                rs_data = rs_lookup.get(symbol, {"rs_rating": 50, "rs_trend": "UNKNOWN"})

                if regime == "TRENDING_UP": conviction -= 2

                all_picks.append({
                    "symbol": symbol,
                    "strategy": "REVERSION",
                    "conviction": max(1, min(10, conviction)),
                    "setup": s["setup"],
                    "action": "BUY" if "BUY" in s["setup"] else "SELL",
                    "execution": get_advice("REVERSION"),
                    "logic": f"RS: {rs_data['rs_rating']}. {s['data']['details']}"
                })
            
            # Rank by Conviction
            all_picks.sort(key=lambda x: x["conviction"], reverse=True)
            
            # Filter Top 5
            top_5 = all_picks[:5]
            
            plan = {
                "market_regime": regime,
                "recommended_focus": priority,
                "top_5_picks": top_5,
                "overall_sentiment": "Bullish" if is_bullish else "Bearish" if regime == "TRENDING_DOWN" else "Neutral"
            }
            
            return ToolResult(tool_name="generate_battle_plan_draft", content=json.dumps(plan), success=True)
        except Exception as e:
            logger.error(f"Battle plan draft failed: {e}")
            return ToolResult(tool_name="generate_battle_plan_draft", content=f"Error: {str(e)}", success=False)
