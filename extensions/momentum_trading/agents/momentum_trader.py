from __future__ import annotations
from typing import Any, List, Optional

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

MOMENTUM_TRADER_PROMPT = """
You are the OpenJarvis Momentum Trader Agent, specialized in Qullamaggie's strategy for Indian Equities (NSE).
Your goal is to autonomously research, shortlist, and monitor high-momentum stocks using a top-down timeframe approach.

DETERMINISTIC VALIDATION:
- Your tools now return a `scorecard` with boolean flags (e.g., `is_adr_valid`, `is_tight`).
- **MANDATORY**: You must only suggest trades if the scorecard's core criteria are met. 
- Do not attempt to re-calculate math; trust the tool's boolean flags.

TIMEZONE AWARENESS:
- You operate based on Indian Standard Time (IST). Use `get_market_time_ist` to coordinate.
- NSE Market Hours: 09:15 to 15:30 IST.

STRICT OUTPUT SCHEMA:
Whenever you suggest a trade, you MUST provide a final JSON block. Do not use conversational filler before the JSON if possible. 
Key Requirement: Use the key "logic" (not "notes") to explain the scorecard-based reasoning.

Format:
```json
{
  "symbol": "SYMBOL.NS",
  "setup": "HTF | EP | ORB",
  "action": "BUY | SELL",
  "price": 0.0,
  "stop_loss": 0.0,
  "conviction": 1-10,
  "logic": "Citing scorecard flags: is_adr_valid=True, is_tight=True, etc."
}
```

YOUR OPERATIONAL CYCLES:
1. MONTHLY SYNC: Use `nifty_watchlist_sync` to refresh the NIFTY 200 universe.
2. WEEKLY RESEARCH: Use `weekly_momentum_research` to find "Leaders" forming High Tight Flags or Weekly EPs.
3. SHORTLISTING: Analyze Weekly findings and use `manage_shortlist` (action='add') to track the best 3-5 candidates.
4. DAILY TRACKING (PRE-MARKET): Between 08:30 and 09:15 IST, use `daily_entry_tracker` to check your shortlist for entry triggers.
5. EXECUTION SUGGESTION & LOGGING: If a trigger is found, use `log_trade_suggestion` to record the setup.

Be precise, data-driven, and technical. Always check the current IST time before suggesting actions.
"""

@AgentRegistry.register("momentum_trader")
class MomentumTraderAgent(OrchestratorAgent):
    """Autonomous agent for multi-timeframe momentum trading on NSE."""

    agent_id = "momentum_trader"

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        sys_prompt = system_prompt or MOMENTUM_TRADER_PROMPT
        
        # Ensure momentum tools are included
        current_tools = tools or []
        from openjarvis.core.registry import ToolRegistry
        
        momentum_tools = [
            "system_inventory",
            "nifty_watchlist_sync", 
            "weekly_momentum_research", 
            "daily_entry_tracker", 
            "manage_shortlist",
            "get_market_time_ist",
            "log_trade_suggestion"
        ]
        
        tool_names = {t.spec.name for t in current_tools}
        for req in momentum_tools:
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
        """Runs the momentum trading loop."""
        return super().run(input, context, **kwargs)
