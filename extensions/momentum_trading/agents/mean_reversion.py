from __future__ import annotations
from typing import Any, List, Optional

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

REVERSION_TRADER_PROMPT = """
You are the OpenJarvis Mean Reversion Trader Agent, specialized in counter-trend and range-bound strategies for Indian Equities (NSE).
Your goal is to identify "stretched" stocks that have deviated significantly from their average and are likely to snap back.

LANGUAGE MANDATE:
- **MANDATORY**: RESPOND ONLY IN ENGLISH. 

TRADING PHILOSOPHY:
- "Buy the Fear": Look for oversold conditions (RSI < 30, below lower Bollinger Band).
- "Sell the Greed": Look for overbought conditions (RSI > 70, above upper Bollinger Band).
- Focus on high-quality NIFTY stocks that are temporarily overextended.

DETERMINISTIC VALIDATION:
- Use the `scorecard` and `conviction_score` provided by your tools.
- Do not trade unless at least two criteria (e.g., RSI and Bollinger Band) align.

STRICT OUTPUT SCHEMA:
Whenever you suggest a trade, you MUST provide a final JSON block:
```json
{
  "symbol": "SYMBOL.NS",
  "setup": "OVERSOLD_REVERSION | OVERBOUGHT_REVERSION",
  "action": "BUY | SELL",
  "price": 0.0,
  "stop_loss": 0.0,
  "conviction": 1-10,
  "logic": "Citing RSI, BB, and Z-Score scorecard flags."
}
```

YOUR OPERATIONAL CYCLES:
1. REVERSION SCAN: Use `nifty_reversion_scan` to find overextended stocks.
2. CONVICTION CHECK: Filter for conviction scores > 7.
3. LOGGING: Use `log_trade_suggestion` to record your findings.

Be contrarian but cautious. Wait for the extreme before suggesting a move.
"""

@AgentRegistry.register("mean_reversion_trader")
class MeanReversionAgent(OrchestratorAgent):
    """Autonomous agent for mean reversion and counter-trend trading on NSE."""

    agent_id = "mean_reversion_trader"

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        sys_prompt = system_prompt or REVERSION_TRADER_PROMPT
        
        current_tools = tools or []
        from openjarvis.core.registry import ToolRegistry
        
        reversion_tools = [
            "nifty_reversion_scan",
            "get_market_time_ist",
            "log_trade_suggestion"
        ]
        
        tool_names = {t.spec.name for t in current_tools}
        for req in reversion_tools:
            if req not in tool_names and ToolRegistry.contains(req):
                t_cls = ToolRegistry.get(req)
                current_tools.append(t_cls())
        
        super().__init__(
            engine,
            model,
            system_prompt=sys_prompt,
            tools=current_tools,
            **kwargs
        )

    def run(
        self,
        input: str,
        context: Optional[AgentContext] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Runs the mean reversion trading loop."""
        return super().run(input, context, **kwargs)
