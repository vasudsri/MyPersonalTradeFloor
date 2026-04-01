#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

# Setup paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "..", "OpenJarvis", "src"))

from openjarvis import Jarvis
import jarvis_trading
jarvis_trading.load_extensions()

from openjarvis.core.registry import ToolRegistry

def main():
    print(f"--- Generating Daily Battle Plan: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
    
    j = Jarvis(model="qwen2.5:7b")
    
    query = """TASK: Generate the JSON Battle Plan. 
    1. Run 'generate_battle_plan_draft'.
    2. Return ONLY that JSON block.
    """

    try:
        response = j.ask(query, agent="master_strategist")
        
        print("\n=== RAW AGENT RESPONSE ===")
        print(response)
        
        # Robust JSON extraction
        json_str = ""
        match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            match = re.search(r'(\{.*\})', response, re.DOTALL)
            if match:
                json_str = match.group(1)

        plan_data = None
        if json_str:
            try:
                plan_data = json.loads(json_str.strip())
            except:
                pass

        # DETERMINISTIC FALLBACK: If agent fails, run the tool directly
        if not plan_data:
            print("\n[SYSTEM] Agent failed to provide clean JSON. Falling back to deterministic tool...")
            tool_cls = ToolRegistry.get("generate_battle_plan_draft")
            result = tool_cls().execute()
            plan_data = json.loads(result.content)

        if plan_data:
            output_path = "extensions/momentum_trading/data/battle_plan.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(plan_data, f, indent=4)
            print(f"\n[SUCCESS] Structured Battle Plan saved to {output_path}")
            print(json.dumps(plan_data, indent=2))
        
    except Exception as e:
        print(f"Error during orchestration: {e}")
    finally:
        j.close()

if __name__ == "__main__":
    main()
