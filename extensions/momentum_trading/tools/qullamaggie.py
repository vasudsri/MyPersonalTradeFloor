import json
import os
import logging
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older python or specific environments if needed
    from datetime import timezone
    ZoneInfo = None

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from extensions.momentum_trading.trading.scanner import QullamaggieScanner
from extensions.momentum_trading.trading.updater import update_watchlist
from extensions.momentum_trading.trading.active_watch import ActiveWatcher

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata") if ZoneInfo else None

def get_ist_now():
    if IST:
        return datetime.now(IST)
    # Manual fallback to UTC+5:30 if ZoneInfo fails
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

@ToolRegistry.register("nifty_watchlist_sync")
class NiftyWatchlistSyncTool(BaseTool):
    """Updates the NIFTY 200 watchlist from NSE."""
    tool_id = "nifty_watchlist_sync"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(name="nifty_watchlist_sync", description="Syncs the NIFTY 200 watchlist from NSE Indices.", parameters={"type": "object", "properties": {}})
    def execute(self, **params) -> ToolResult:
        update_watchlist()
        return ToolResult(tool_name="nifty_watchlist_sync", content="NIFTY 200 Watchlist updated successfully.", success=True)

@ToolRegistry.register("weekly_momentum_research")
class WeeklyMomentumResearchTool(BaseTool):
    """Scans for Weekly HTF/EP setups."""
    tool_id = "weekly_momentum_research"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(name="weekly_momentum_research", description="Scans the NIFTY 200 for Weekly momentum setups (HTF/EP).", parameters={"type": "object", "properties": {}})
    def execute(self, **params) -> ToolResult:
        scanner = QullamaggieScanner(interval="1wk")
        results = scanner.scan()
        return ToolResult(tool_name="weekly_momentum_research", content=json.dumps(results), success=True)

@ToolRegistry.register("daily_entry_tracker")
class DailyEntryTrackerTool(BaseTool):
    """Monitors shortlisted stocks for Daily entry triggers."""
    tool_id = "daily_entry_tracker"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(name="daily_entry_tracker", description="Monitors the current shortlist for Daily entry triggers (Breakouts/Tightness).", parameters={"type": "object", "properties": {}})
    def execute(self, **params) -> ToolResult:
        import sys
        import io
        # Capture the print output from ActiveWatcher
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        try:
            watcher = ActiveWatcher()
            watcher.analyze_entry_conditions()
            output = new_stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return ToolResult(tool_name="daily_entry_tracker", content=output, success=True)

@ToolRegistry.register("manage_shortlist")
class ManageShortlistTool(BaseTool):
    """Adds or removes stocks from the active watch shortlist."""
    tool_id = "manage_shortlist"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="manage_shortlist", 
            description="Adds or removes symbols from the active watch shortlist.", 
            parameters={
                "type": "object", 
                "properties": {
                    "action": {"type": "string", "enum": ["add", "remove", "clear"]},
                    "symbols": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["action"]
            }
        )
    def execute(self, **params) -> ToolResult:
        config_path = "extensions/momentum_trading/configs/active_watch.json"
        action = params["action"]
        symbols = params.get("symbols", [])
        
        with open(config_path, "r") as f:
            data = json.load(f)
        
        current_list = set(data.get("shortlist", []))
        
        if action == "add":
            # Automatically append .NS if missing
            formatted_symbols = [s if s.endswith(".NS") else f"{s}.NS" for s in symbols]
            current_list.update(formatted_symbols)
        elif action == "remove":
            # Check both with and without suffix for removal
            to_remove = set(symbols) | {f"{s}.NS" for s in symbols}
            current_list.difference_update(to_remove)
        elif action == "clear":
            current_list = set()
            
        data["shortlist"] = sorted(list(current_list))
        with open(config_path, "w") as f:
            json.dump(data, f, indent=4)
            
        return ToolResult(tool_name="manage_shortlist", content=f"Shortlist updated. Current: {data['shortlist']}", success=True)

@ToolRegistry.register("get_market_time_ist")
class MarketTimeISTTool(BaseTool):
    """Returns the current time in IST to coordinate with NSE hours."""
    tool_id = "get_market_time_ist"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(name="get_market_time_ist", description="Returns the current date and time in IST (India).", parameters={"type": "object", "properties": {}})
    def execute(self, **params) -> ToolResult:
        now = get_ist_now()
        return ToolResult(tool_name="get_market_time_ist", content=f"Current IST Time: {now.strftime('%Y-%m-%d %H:%M:%S')} (Market hours: 09:15-15:30 IST)", success=True)

@ToolRegistry.register("list_available_charts")
class ListStockImagesTool(BaseTool):
    """Lists all uploaded stock chart images."""
    tool_id = "list_available_charts"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(name="list_available_charts", description="Lists all available stock chart images in the data directory.", parameters={"type": "object", "properties": {}})
    def execute(self, **params) -> ToolResult:
        base_dir = "extensions/momentum_trading/data/stockimages"
        if not os.path.exists(base_dir):
            return ToolResult(tool_name="list_available_charts", content="No image directory found.", success=False)
        files = os.listdir(base_dir)
        return ToolResult(tool_name="list_available_charts", content=f"Available charts: {files}", success=True)

from pydantic import BaseModel, Field, validator
from typing import Literal

class TradeSuggestionSchema(BaseModel):
    symbol: str = Field(..., description="NSE Stock Symbol with .NS suffix")
    setup: Literal["HTF", "EP", "ORB"]
    action: Literal["BUY", "SELL", "SHORT"]
    price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    conviction: int = Field(..., ge=1, le=10)
    logic: str = Field("", alias="notes")

    class Config:
        populate_by_name = True

@ToolRegistry.register("log_trade_suggestion")
class TradeLoggerTool(BaseTool):
    """Logs a trade suggestion to the local trade log CSV."""
    tool_id = "log_trade_suggestion"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="log_trade_suggestion", 
            description="Logs a high-conviction trade suggestion to the system for performance tracking.", 
            parameters={
                "type": "object", 
                "properties": {
                    "symbol": {"type": "string"},
                    "setup": {"type": "string", "enum": ["HTF", "EP", "ORB"]},
                    "action": {"type": "string", "enum": ["BUY", "SELL", "SHORT"]},
                    "price": {"type": "number"},
                    "stop_loss": {"type": "number"},
                    "conviction": {"type": "integer", "minimum": 1, "maximum": 10},
                    "notes": {"type": "string"}
                },
                "required": ["symbol", "setup", "action", "price", "stop_loss", "conviction"]
            }
        )
    def execute(self, **params) -> ToolResult:
        import csv
        
        # 1. Strict Validation using Pydantic
        try:
            trade = TradeSuggestionSchema(**params)
        except Exception as e:
            return ToolResult(tool_name="log_trade_suggestion", content=f"Validation Error: {str(e)}", success=False)

        log_dir = "extensions/momentum_trading/data"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "agent_trade_suggestions.csv")
        
        file_exists = os.path.isfile(log_path)
        now = get_ist_now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Symbol", "Setup", "Action", "Price", "SL", "Conviction", "Notes"])
            writer.writerow([
                now, 
                trade.symbol, 
                trade.setup, 
                trade.action, 
                trade.price, 
                trade.stop_loss, 
                trade.conviction, 
                trade.notes
            ])
            
        return ToolResult(tool_name="log_trade_suggestion", content=f"Trade suggestion for {trade.symbol} logged successfully.", success=True)

@ToolRegistry.register("analyze_chart_technicals")
class AnalyzeChartTechnicalsTool(BaseTool):
    """Performs a deep technical analysis on a specific chart image."""
    tool_id = "analyze_chart_technicals"
    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="analyze_chart_technicals", 
            description="Analyzes a specific chart image for PIVOTs, Supply/Demand, EMAs, and Stochastics.", 
            parameters={
                "type": "object", 
                "properties": {
                    "file_name": {"type": "string", "description": "The exact name of the image file to analyze."}
                },
                "required": ["file_name"]
            }
        )
    def execute(self, **params) -> ToolResult:
        # Note: This tool simply returns the file path and metadata. 
        # The Agent's vision engine will do the actual analysis.
        path = os.path.join("extensions/momentum_trading/data/stockimages", params["file_name"])
        if not os.path.exists(path):
            return ToolResult(tool_name="analyze_chart_technicals", content=f"File {params['file_name']} not found.", success=False)
        
        # We return the path and a prompt instruction for the agent
        return ToolResult(tool_name="analyze_chart_technicals", content=f"IMAGE_PATH:{path}", success=True)
