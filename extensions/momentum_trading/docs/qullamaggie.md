# Qullamaggie's Momentum Trading Strategy

This document synthesizes the core trading methodology of Kristjan Qullamaggie (jfsrev), as documented in his blog and video tutorials. This strategy is primarily built on momentum, price-volume relationships, and volatility contraction.

---

## 1. Technical Framework
The strategy utilizes three primary Exponential Moving Averages (EMAs) to identify and manage trends:
*   **10-day EMA:** Used for the fastest-moving stocks and as a trailing stop for the strongest trends.
*   **20-day EMA:** The "primary trend guard." Most setups should be above or hugging this average.
*   **50-day EMA:** Used for medium-term trend confirmation; many stocks reset and bounce off this level.

---

## 2. Core Trading Setups

### Setup A: High Tight Flag (HTF) / Breakouts
This is the "Bread and Butter" setup. It identifies stocks that have already shown extreme strength and are now "resting."
*   **Pre-Condition:** A massive "First Leg" up of 30-100%+ within 1-3 months.
*   **The Consolidation:** A sideways "flag" or "pennant" where volatility contracts (VCP).
*   **The "Tightness":** Price should be hugging the 10 or 20 EMA, with daily ranges getting smaller.
*   **Volume:** Volume must "dry up" during the consolidation.
*   **Entry:** Buy the breakout above the high of the tight consolidation range on expanding volume.
*   **The "Cheat":** Entering just before the breakout when the price is extremely tight and the 10/20 EMA is "pushing" price up.

### Setup B: Episodic Pivots (EP)
Trading massive gap-ups driven by structural shifts or fundamental catalysts.
*   **Catalyst:** Earnings surprise, contract win, new product, or major sector theme (e.g., AI, Crypto, Biotech).
*   **The Gap:** Price gaps up >10% (ideally >15-20%) on **massive volume** (multi-month or multi-year volume high).
*   **Entry:** Buy at the market open or on a breakout of the "Opening Range" (e.g., first 5-15 mins high) of the gap-up day.
*   **The "Hold":** These are often multi-month moves if the catalyst is strong.

### Setup C: Parabolic Shorts (Advanced)
Shorting extreme exhaustion moves.
*   **Pre-Condition:** A stock that has gone "vertical," becoming extremely extended above its 10/20/50 EMAs.
*   **Trigger:** The "First Red Day" (FRD) after a parabolic run.
*   **Entry:** Short on the breakdown of the previous day's low or after a failed "exhaustion" rally.
*   **Caution:** This is a counter-trend setup and carries high risk.

---

## 3. Risk Management & Position Sizing

### Stop Loss Placement
*   **Breakouts:** The stop is placed at the **Low of the Day (LOD)** of the breakout. If the breakout day is very small, use the low of the previous day.
*   **Episodic Pivots:** The stop is placed at the **Low of the Day** of the massive gap-up.
*   **Hard Rule:** If a stock moves 2-3 Average True Ranges (ATR) in your favor, move the stop to **Breakeven (BE)**.

### Position Sizing
*   **Risk per Trade:** 0.25% to 1% of total account equity.
*   **Calculation:** `Position Size = (Account Risk Amount) / (Entry Price - Stop Price)`.
*   **Account Concentration:** Qullamaggie often holds 5-10 positions, concentrating capital in the highest conviction names.

---

## 4. Trade Management (The "Sell Into Strength" Model)

*   **Initial Profit Take:** Sell **1/3 to 1/2 of the position** after 3 to 5 days of a strong move (this locks in gains and pays for the trade).
*   **The Trailing Stop:** Use the **10 EMA or 20 EMA** for the remaining portion. 
    *   If the stock is a "Superstock" (moving very fast), trail with the **10 EMA**.
    *   If it's a slower trend, use the **20 EMA**.
*   **The Exit:** Close the remaining position when the price **closes below** the chosen trailing EMA.
*   **Time Stop:** If a breakout fails to move within 2-3 days, exit or trim. The best breakouts "work immediately."

---

## 5. Daily Routine & Scanning

### Scanning Criteria (TC2000 or Similar)
1.  **Top % Gainers (1 month, 3 months, 6 months):** Find the "leaders" with the most relative strength.
2.  **Price > $5:** Avoid low-liquidity penny stocks.
3.  **Volume > 500k-1M shares/day:** Ensure liquidity for exits.
4.  **Distance from 20/50 EMA:** Look for stocks that have pulled back or are tight near these levels.

### The Routine
*   **Pre-Market:** Look for Gaps (EP candidates). Check news catalysts.
*   **Intraday:** Focus on entries in the first 90 minutes. Scan for breakout alerts.
*   **Post-Market:** The "Deep Work." Scan through the top 500-1000 % gainers manually to find the "Tight Flags." 

---

## 6. Backtesting & Forward Testing Template

When testing these setups, track the following variables:
1.  **Setup Type:** HTF or EP?
2.  **Distance to 20 EMA:** How "extended" was it at entry?
3.  **Volume on Breakout:** Ratio of breakout volume to 20-day average volume.
4.  **The Flag Duration:** How many days did it consolidate?
5.  **Market Condition:** Is the broad market (SPY/QQQ) above its 20/50 EMA?
6.  **Exit Reason:** Hit trailing EMA, Hit Stop, or Time Stop?
