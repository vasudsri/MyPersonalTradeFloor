# Momentum Trader: Private Extensions for OpenJarvis

## 1. Overview
**Momentum Trader** is a specialized extension suite for the [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) agentic framework. It transforms OpenJarvis from a general-purpose assistant into a high-conviction momentum trading companion focused on the Indian Equities (NSE) market.

This system implements the trading methodologies of **Kristjan Qullamaggie** and **Stockbee**, specifically targeting:
*   **High Tight Flags (HTF):** Consolidation patterns after explosive moves.
*   **Episodic Pivots (EP):** Massive gap-ups driven by fundamental catalysts.
*   **Champion ORB:** A specialized 5-minute Opening Range Breakout strategy.

---

## 2. Architecture: The "Overlay" Pattern
This repository utilizes an **Overlay Architecture**. It is designed to sit *on top* of a standard OpenJarvis installation without modifying its core source code.

### Key Benefits:
*   **Decoupled Logic:** Your private trading strategies, scanners, and personal watchlists remain in this private repository.
*   **Upstream Compatibility:** You can update the core OpenJarvis engine (`git pull upstream main`) without risking conflicts with your trading logic.
*   **Shim Entry Point:** The `jarvis_trading.py` script acts as a wrapper that injects these extensions into the OpenJarvis runtime at startup.

---

## 3. The Momentum Trader Agent
The core of this extension is the `momentum_trader` agent. It is an autonomous orchestrator designed to handle the full trading lifecycle:

*   **Timezone Aware:** Operates natively in Indian Standard Time (IST) for NSE market alignment.
*   **Multi-Timeframe Analysis:** Performs Weekly scans for setup identification and Daily scans for entry execution.
*   **Shortlist Management:** Maintains a "hot list" of 3-5 high-conviction stocks.
*   **Vision-Driven Technical Confirmation:** Replicates high-end vision workflows (similar to Claude-based chart analysis) to connect directly with TradingView charts. It doesn't just "see" patterns; it identifies exact entry/exit levels and technical pivots (R1/S1, Supply/Demand zones) by analyzing live chart captures.

### Operational Cycles:
1.  **Monthly Sync:** Refreshes the NIFTY 200 universe.
2.  **Weekly Research:** Identifies leaders forming HTFs or Weekly EPs.
3.  **Daily Tracking:** Monitors the shortlist for breakout triggers between 08:30 and 09:15 IST.
4.  **Vision Validation:** The `chart_validator` agent performs a final visual confirmation of all high-conviction setups before they are added to the daily Battle Plan.

---

## 4. Custom Tools & Capabilities
The extension adds several specialized tools to the OpenJarvis registry:

*   `weekly_momentum_research`: Scans NIFTY 200 for Qullamaggie-style setups.
*   `daily_entry_tracker`: Checks for real-time price tightness and breakout triggers.
*   `manage_shortlist`: Persistently tracks your active trading candidates.
*   `analyze_chart_technicals`: Deep-dive analysis of chart images for technical confirmation, extracting exact price levels for stops and targets.
*   `list_available_charts`: Automatically indexes local or remote chart screenshots for the vision agent.
*   `system_inventory`: Categorizes all available tools into "Built-in" and "Custom" (Momentum) categories.

---

## 5. Getting Started

### Prerequisites
*   A working installation of [OpenJarvis](https://github.com/open-jarvis/OpenJarvis).
*   Python 3.10+ with `uv` installed.

### Installation & Linking
1. Clone this repository adjacent to your OpenJarvis directory.
2. Run the setup script to link the extension:
   ```bash
   chmod +x setup_extension.sh
   ./setup_extension.sh /path/to/your/OpenJarvis
   ```

### Usage
Always use the `jarvis_trading.py` entry point to ensure the momentum extensions are loaded:

```bash
# Ask the agent to perform weekly research
uv run python jarvis_trading.py ask "Run my weekly momentum research and tell me which stocks are tight" --agent momentum_trader

# Check if any shortlist stocks are triggering
uv run python jarvis_trading.py ask "Check my shortlist for daily entry triggers" --agent momentum_trader
```

---

## 6. Strategy Documentation
Detailed technical rules for the implemented strategies can be found in:
*   `extensions/momentum_trading/docs/qullamaggie.md`: High Tight Flags, Episodic Pivots, and Position Sizing.
*   `GEMINI.md`: Champion ORB strategy parameters and historical top performers.
