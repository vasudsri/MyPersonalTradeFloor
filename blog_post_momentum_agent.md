# The Momentum Trader: System Architecture & Strategy Evolution

## 1. Vision: A Private Quantitative Trade Floor
**Momentum Trader** is a specialized extension for the OpenJarvis framework, designed to transform a personal workstation into an institutional-grade trading floor for Indian Equities (NSE). The project's mission is to exploit structural market anomalies—specifically **Opening Range Breakouts (ORB)** and **Volatility Contraction Patterns (VCP)**—using automated agents, probabilistic models, and mathematical risk management.

---

## 2. Core Architecture (The Model-Driven Evolution)
The system has evolved from a "rule-based" scanner into a sophisticated "model-driven" architecture:
*   **The Trading Floor (`floor.py`):** The orchestration layer that consolidates multiple strategy engines (Momentum, Mean Reversion, Fundamental Momentum).
*   **Market Regime AI (`regime.py`):** Utilizes **Gaussian Hidden Markov Models (HMM)** to dynamically classify the NIFTY 50 index into states (e.g., BULLISH_TRENDING, SIDEWAYS_CHOPPY, BEARISH_VOLATILE) and dictate the daily strategy focus and risk multipliers.
*   **Dual-Universe Scanners:**
    *   **Dynamic Universe:** Scans the NIFTY 500 for "High-Octane" setups (Volume > 100k, ADR > 4%).
    *   **Comprehensive Universe:** Scans all 2,000+ NSE equities, applying liquidity filters before enriching candidates with fundamental data (Market Cap, ROE) for micro-cap discovery.
*   **Risk & Portfolio Engine (`risk.py` & `portfolio.py`):** A mathematical core using the **Fractional Kelly Criterion** for position sizing, coupled with a virtual portfolio manager that tracks live PnL across different strategy types.
*   **Execution Bridge (`execution.py`):** Integrates with **OpenAlgo** to translate generated "Battle Plans" into live, automated order routing with brokers (e.g., Groww).

---

## 3. Core Strategy Engines
### A. Fundamental Momentum
Our newest and most comprehensive engine. It targets high-growth SMEs and mid-caps by scanning the entire NSE universe.
*   **Criteria:** Market Cap (10M - 2T INR), ROE (15-20%), RSI(14) > 60, Price > EMA50, EMA50 > EMA200, and Price > Intraday VWAP.

### B. Qullamaggie Breakouts (Momentum)
Scanning the high-ADR dynamic universe for "High Tight Flags" and "Episodic Pivots" on Daily timeframes, utilizing an adaptive **Kalman Filter** to track the true price trend.

### C. Mean Reversion
A counter-trend strategy deployed primarily when the HMM detects a "SIDEWAYS_CHOPPY" regime. It buys support and sells resistance when momentum breakouts are statistically likely to fail.

---

## 4. Critical Decisions & Pivots
### Decision: HMM Regime Detection over Simple EMAs
Initially, the system used basic moving averages (EMA20/50) to determine market direction. 
*   **Finding:** EMAs lag significantly in choppy markets, leading to "whipsaw" losses in momentum trades.
*   **Action:** We implemented a Hidden Markov Model (HMM) that analyzes both *Returns* and *Volatility Range*. The system now intelligently "turns off" momentum scanners and switches to Mean Reversion during sideways regimes.

### Decision: Decoupling UI from the Core
To maintain a strict layered architecture, we avoided deeply embedding custom trading UIs into the generic OpenJarvis framework.
*   **Action:** We built a standalone **Trading Radar** dashboard. The backend (`morning_battle_plan.py`) generates a `battle_plan.json` artifact containing real-time NSE prices, RS rankings, and dynamic stop-losses (0.5x ADR), which is cleanly consumed by a dedicated React frontend page.

---

## 5. Recent Implementation Milestones
*   **Trading Radar Dashboard:** A high-fidelity, real-time React dashboard visualizing the day's HMM state, active portfolio PnL (assuming fixed ₹10,000 investments), and top 15 scanner setups.
*   **Automated Orchestration:** `master_orchestrator.py` unifies the daily flow: HMM Prediction -> Dual-Universe Scan -> Kelly Sizing -> OpenAlgo Execution.
*   **Dynamic Stop Losses:** Replaced static 2% stops with volatility-adjusted stops based on the asset's Average Daily Range (0.5x ADR).

---

## 6. The Roadmap (Yet to Implement)
While the foundation is solid, the following enhancements are in the pipeline:
*   **[ ] Mean Reversion 2.0:** Transition from RSI/Bollinger Bands to modeling mean reversion using the **Ornstein-Uhlenbeck** process for dynamic position sizing based on mean-pull strength.
*   **[ ] Volatility Guardrails (GARCH):** Introduce GARCH modeling to forecast next-day volatility and preemptively adjust Kelly sizing during extreme events.
*   **[ ] Live Execution Verification:** Transition the OpenAlgo bridge from "Dry Run" mode to live paper-trading for one week to verify slippage and execution latency.
*   **[ ] Monte Carlo Stress Testing:** Implement Geometric Brownian Motion (GBM) to simulate price paths and stress-test the system's Max Drawdown over 10,000 iterations.

---
*Last Updated: Monday, April 6, 2026*
*Author: Gemini Trading Agent*
