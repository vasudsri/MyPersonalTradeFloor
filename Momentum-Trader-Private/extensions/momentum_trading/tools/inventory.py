import json
import os
from typing import List, Dict, Any
from openjarvis.core.registry import ToolRegistry, AgentRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec

@ToolRegistry.register("system_inventory")
class SystemInventoryTool(BaseTool):
    """Provides a factual list of all registered Agents and Tools."""
    tool_id = "system_inventory"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="system_inventory", 
            description="Returns a categorized list of all built-in and custom Agents and Tools registered in OpenJarvis.", 
            parameters={"type": "object", "properties": {}}
        )

    def execute(self, **params) -> ToolResult:
        def categorize(registry):
            built_in = []
            custom = []
            for key in sorted(registry.keys()):
                try:
                    obj = registry.get(key)
                    module = obj.__module__
                    if "extensions.momentum_trading" in module:
                        custom.append(key)
                    else:
                        built_in.append(key)
                except:
                    built_in.append(key)
            return {"built_in": built_in, "custom": custom}

        data = {
            "agents": categorize(AgentRegistry),
            "tools": categorize(ToolRegistry)
        }
        
        return ToolResult(tool_name="system_inventory", content=json.dumps(data), success=True)
