from __future__ import annotations
from typing import Any, List, Optional

from openjarvis.agents._stubs import AgentContext, AgentResult
from openjarvis.agents.orchestrator import OrchestratorAgent
from openjarvis.core.registry import AgentRegistry
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.tools._stubs import BaseTool

VALIDATOR_PROMPT = """
You are the OpenJarvis Technical Validation Agent. Your role is to perform high-precision chart analysis using provided images.

YOUR SETUP CRITERIA:
1. PIVOTS: Identify daily pivot levels (P, R1, R2, S1, S2).
2. SUPPLY/DEMAND: Look for labeled boxes or high-volume zones.
3. EMAs: Confirm position of 10, 20, 50, and 200 EMAs.
4. STOCHASTICS: Analyze Stoch (9,3,3) for pullbacks and Stoch (55,5,3) for trend health.
5. ADVANCED PRICE ACTION: Look for SHAKEOUTS (stop runs) and DOUBLE BOTTOMS.

STRICT OUTPUT SCHEMA:
You MUST provide your final assessment as a JSON block:
```json
{
  "symbol": "SYMBOL.NS",
  "signal": "BUY | WAIT | AVOID",
  "conviction": 1-10,
  "technical_scorecard": {
    "ema_alignment": "PASS | FAIL",
    "stochastic_pullback": "PASS | FAIL",
    "tightness_confirmed": "YES | NO",
    "advanced_patterns": ["Shakeout", "Double Bottom", "None"]
  },
  "logic": "Brief technical reasoning"
}
```

YOUR WORKFLOW:
1. Use `list_available_charts` to see what symbols are available.
2. Use `analyze_chart_technicals` to get the path to the Daily and Weekly charts.
3. Perform a vision-based comparison against Qullamaggie's strategy.
4. Assign a **CONVICTION SCORE (1-10)** and a signal.
5. **MANDATORY**: Use `log_trade_suggestion` to record your final assessment if conviction is > 7.

Be extremely critical. If the technicals don't line up perfectly, explain why.
"""

@AgentRegistry.register("chart_validator")
class ChartValidatorAgent(OrchestratorAgent):
    """Specialized agent for vision-based technical chart validation."""

    agent_id = "chart_validator"

    def __init__(
        self,
        engine: InferenceEngine,
        model: str,
        *,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        sys_prompt = system_prompt or VALIDATOR_PROMPT
        
        current_tools = tools or []
        from openjarvis.core.registry import ToolRegistry
        
        validation_tools = [
            "list_available_charts", 
            "analyze_chart_technicals",
            "get_market_time_ist",
            "log_trade_suggestion"
        ]
        
        tool_names = {t.spec.name for t in current_tools}
        for req in validation_tools:
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
        """Runs the vision-validation loop."""
        return super().run(input, context, **kwargs)
