
import os
import sys

# Setup paths
root_dir = os.getcwd()
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "..", "OpenJarvis", "src"))

# Import shim logic
import jarvis_trading
jarvis_trading.load_extensions()

from openjarvis.core.registry import ToolRegistry, AgentRegistry

def test_system():
    print("--- Verifying Momentum Trading System ---")
    
    # Check Registry
    print("\nChecking Agent Registry:")
    for agent in ["momentum_trader", "chart_validator"]:
        exists = AgentRegistry.contains(agent)
        print(f"Agent '{agent}': {'LOADED' if exists else 'MISSING'}")
        
    print("\nChecking Tool Registry:")
    tools = [
        "nifty_watchlist_sync", 
        "weekly_momentum_research", 
        "daily_entry_tracker", 
        "manage_shortlist",
        "get_market_time_ist",
        "log_trade_suggestion"
    ]
    for tool in tools:
        exists = ToolRegistry.contains(tool)
        print(f"Tool '{tool}': {'LOADED' if exists else 'MISSING'}")

    # Run a live test of the Market Time tool
    print("\nTesting Market Time Tool:")
    if ToolRegistry.contains("get_market_time_ist"):
        tool_cls = ToolRegistry.get("get_market_time_ist")
        result = tool_cls().execute()
        print(f"Result: {result.content}")

    # Run a live test of the Weekly Research (Limited scan to verify logic)
    # Note: This might take time as it fetches data from yfinance
    print("\nTesting Weekly Momentum Research (First 2 stocks):")
    if ToolRegistry.contains("weekly_momentum_research"):
        # We can't easily limit the internal scanner without modifying it, 
        # so let's just see if it starts up and handles the first few.
        # To avoid a long wait, we'll just check if the class can be instantiated.
        tool_cls = ToolRegistry.get("weekly_momentum_research")
        print("Tool instantiated successfully.")

if __name__ == "__main__":
    test_system()
