from __future__ import annotations
from typing import Any, List, Optional

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

STRATEGIST_PROMPT = """
You are the OpenJarvis Master Strategist. 

GOAL:
- Generate a structured Daily Battle Plan.
- Use 'generate_battle_plan_draft' to get the current technical state and initial picks.
- Use 'get_execution_advice' for EACH of the top 5 picks to get specific trade orders.
- Integrate the advice into the "execution" field of each pick.

LANGUAGE MANDATE:
- RESPOND ONLY IN ENGLISH. 

STRICT OUTPUT SCHEMA (FOLLOW THIS EXACTLY):
```json
{
  "market_regime": "TRENDING_UP",
  "recommended_focus": "MOMENTUM",
  "top_5_picks": [
    {
      "symbol": "HAL.NS",
      "strategy": "MOMENTUM",
      "conviction": 9,
      "setup": "HTF",
      "action": "BUY",
      "execution": {
         "entry": "Breakout above Yesterday's High",
         "stop_loss": "Low of the day",
         "exit": "Sell 50% at +5%, trail rest with 10EMA"
      },
      "logic": "RS Rating 98, high conviction scorecard."
    }
  ],
  "overall_sentiment": "Bullish"
}
```

EXECUTE: 
1. Run 'generate_battle_plan_draft'.
2. For each symbol in top_5_picks, run 'get_execution_advice'.
3. Synthesize the final Battle Plan JSON block.
"""

@AgentRegistry.register("master_strategist")
class MasterStrategistAgent(OrchestratorAgent):
    """Senior portfolio manager agent."""

    agent_id = "master_strategist"

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        sys_prompt = system_prompt or STRATEGIST_PROMPT
        
        current_tools = tools or []
        from openjarvis.core.registry import ToolRegistry
        
        essential_tools = [
            "generate_battle_plan_draft",
            "get_execution_advice",
            "log_trade_suggestion"
        ]
        
        tool_names = {t.spec.name for t in current_tools}
        for req in essential_tools:
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
        """Runs the strategist decision loop."""
        return super().run(input, context, **kwargs)
