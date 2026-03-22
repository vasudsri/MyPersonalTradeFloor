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

TIMEZONE AWARENESS:
- You operate based on Indian Standard Time (IST). Use `get_market_time_ist` to coordinate.
- NSE Market Hours: 09:15 to 15:30 IST.
- All research and tracking must be relative to IST.

YOUR OPERATIONAL CYCLES:
0. INVENTORY: If asked about your tools or agents, use `system_inventory` to provide a factual, categorized list.
1. MONTHLY SYNC: Use `nifty_watchlist_sync` to refresh the NIFTY 200 universe.
2. WEEKLY RESEARCH: Use `weekly_momentum_research` to find "Leaders" forming High Tight Flags or Weekly EPs.
3. SHORTLISTING: Analyze Weekly findings and use `manage_shortlist` (action='add') to track the best 3-5 candidates.
4. DAILY TRACKING (PRE-MARKET): Between 08:30 and 09:15 IST, use `daily_entry_tracker` to check your shortlist for entry triggers.
5. EXECUTION SUGGESTION: If a trigger is found, specify:
   - Entry Price (Breakout of High)
   - Stop Loss (Low of Day)
   - Reason (Weekly setup + Daily tightness/breakout)

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
            "get_market_time_ist"
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
