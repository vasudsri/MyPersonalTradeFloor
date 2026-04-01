# Trader Project: Roadmap & To-Do List

This document outlines the strategic roadmap for validating, testing, and optimizing the **Momentum Trader** system for Indian Equities (NSE).

---

## 1. Strategy Validation & Knowledge Base
**Goal:** Ensure the coded logic aligns strictly with verified Qullamaggie/Stockbee methodologies.

- [x] **Cross-Reference Qullamaggie Sources:**
    - [x] Review "The 4 Main Setups" video and blog posts.
    - [x] Verify EMA settings (10, 20, 50) and ADR (Average Daily Range) calculations.
    - [x] Confirm "Tightness" definitions (Volatility Contraction Patterns).
- [x] **Document Strategy Edge:**
    - [x] Explicitly define the "Surprise" factor for Episodic Pivots (EP).
    - [x] Define "Relative Strength" ranking vs. NIFTY 50/500 Index.
- [x] **Refine Champion ORB Logic:**
    - [x] Re-verify the 5-min ORB breakout rules against the GEMINI.md memories.
    - [x] Document the "Time-of-Day" filter (First 90 minutes).

---

## 2. 10-Year Index Backtesting
**Goal:** Validate the strategy's robustness across multiple market cycles (2015-2025) using Index data.

- [x] **Data Acquisition:**
    - [x] Fetch/Download 10 years of NIFTY 50 and NIFTY 500 Daily/Weekly data. (Sources: `NIFTY_UNIFIED.parquet` (Daily) and `NIFTY 50_5minutedata.csv` (5-min))
    - [x] Store as Parquet for high-performance retrieval.
- [x] **Baseline Simulation:**
    - [x] Run the "Weekly Research" scanner retroactively over the index data.
    - [x] Simulate entries based on "Daily Tightness" triggers.
- [x] **Cycle Analysis:**
    - [x] Identify performance during Bull markets (2017, 2021).
    - [x] Identify performance during Bear/Sideways markets (2016, 2020, 2022).
    - [x] Measure "Time to Recovery" (Max Drawdown duration).

---

## 3. Quantitative Performance Metrics
**Goal:** Move beyond PnL and measure the strategy's statistical validity.

- [x] **Implement Performance Ratios:**
    - [x] **Sharpe Ratio:** Measure risk-adjusted returns (using NSE 91-day T-Bill as risk-free rate).
    - [x] **Expectancy:** `(Win% * AvgWin) - (Loss% * AvgLoss)`. Target > 0.5.
    - [x] **Profit Factor:** Gross Profits / Gross Losses.
    - [x] **Max Drawdown (MDD):** Peak-to-trough decline.
- [x] **Trade Distribution Analysis:**
    - [x] Plot PnL distribution (Looking for "Fat Tails" - small losses, huge wins).
    - [x] Calculate "Average Hold Time" for Winners vs. Losers.

---

## 4. Automation & Agentic Enhancements
**Goal:** Improve the autonomy of the `momentum_trader` agent.

- [x] **Automated Performance Logging:**
    - [x] Create a tool to automatically log trade suggestions to `data/trade_log.csv`.
- [x] **Enhanced Vision Validation:**
    - [x] Improve `chart_validator` to detect "Double Bottoms" and "Shakeouts" near EMAs.
- [x] **Daily Routine Scheduler:**
    - [x] Setup a cron/launchd job to trigger the "Pre-Market Check" at 08:45 IST daily.

---

## 5. Deployment & Private Hosting
**Goal:** Ensure the system runs reliably on personal hardware.

- [x] **Server Setup:**
    - [x] Deploy as a background daemon on the local Mac using `launchd`.
    - [ ] Configure `tailscale` or similar for secure remote monitoring of the agent.
- [x] **Backup Strategy:**
    - [x] Automated daily backup of `configs/` and `data/` to a private cloud/git branch.

---

## 7. Mean Reversion & Multi-Strategy Orchestration
**Goal:** Complement Momentum with Reversion and create a unified "Battle Plan" for the day.

- [x] **Mean Reversion Logic:**
    - [x] Implement `MeanReversionScanner` with RSI, Bollinger Bands, and Z-Score.
- [x] **Trading Floor Manager:**
    - [x] Create `TradingFloor` class to consolidate Momentum and Reversion scans into a single técnico report.
- [x] **Master Strategist Agent:**
    - [x] Implement `MasterStrategistAgent` to synthesize findings and pick the absolute best 3-5 trades based on market regime.
- [x] **Battle Plan State:**
    - [x] Create `morning_battle_plan.py` to produce a structured `battle_plan.json` for dashboard/algo consumption.

---

## 9. Mathematical Risk & Capital Allocation
**Goal:** Maximize long-term growth using the Kelly Criterion while maintaining institutional-grade safety.

- [x] **Dynamic Edge Extraction:**
    - [x] Build a tool to parse backtest logs and calculate Win Rate ($p$) and Win/Loss Ratio ($b$) per strategy. (Implemented in `risk.py`)
- [x] **Kelly Sizing Engine:**
    - [x] Implement a `RiskManager` using Fractional Kelly logic.
    - [x] Calculate "Optimal Share Quantity" for each pick in the Battle Plan based on Account Capital.
- [ ] **Volatility Guardrails:**
    - [ ] Implement a "Maximum Drawdown Cap" to override Kelly bets during high-volatility regimes.

