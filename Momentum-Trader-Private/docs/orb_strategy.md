# Champion ORB Strategy (NSE Indian Equities)

The Champion ORB is a specialized high-probability Opening Range Breakout (ORB) strategy optimized for the NIFTY 100 constituents.

---

## 1. Technical Setup
*   **Timeframe:** 5-minute Intraday charts.
*   **Indicators:**
    *   **EMA 20 (Daily):** Used as the primary trend filter.
    *   **Stochastic (9,3,3):** Used to identify pullbacks within the intraday trend.
    *   **ATR (14):** Used for calculating the dynamic trailing stop.

---

## 2. Entry Rules
*   **The Opening Range:** Defined by the high and low of the first 5-minute candle (09:15 - 09:20 IST).
*   **The Entry Window:** Entries are only permitted between **09:20 and 10:30 IST** (The first 90 minutes).
*   **Long Entry Criteria:**
    1.  Price must be trading above the 5-min ORB High.
    2.  Daily Trend Filter: Current price must be above the **Daily EMA 20**.
    3.  Stochastic Filter: Intraday Stochastic (9,3,3) must show a pullback (Oversold < 20) and a bullish crossover (%K > %D).
*   **Short Entry Criteria:**
    1.  Price must be trading below the 5-min ORB Low.
    2.  Daily Trend Filter: Current price must be below the **Daily EMA 20**.
    3.  Stochastic Filter: Intraday Stochastic (9,3,3) must show a pullback (Overbought > 80) and a bearish crossover (%K < %D).

---

## 3. Risk Management & Exits
*   **Initial Stop Loss:** Placed at the opposite side of the 5-min ORB (e.g., ORB Low for Longs).
*   **Trailing Stop:** A dynamic trailing stop of **1.8x ATR** from the highest price (for longs) or lowest price (for shorts) reached during the trade.
*   **Profit Taking (Optional):** MACD or Stochastic extremes can be used for early exits if the move becomes parabolic.
*   **Time Exit:** All positions are closed at **15:20 IST** (EOD) if not stopped out earlier.

---

## 4. Best Performers (2015-2025)
Based on historical backtesting on the NIFTY 100:
*   **ADANIENT:** Win Rate 67%, PnL +53%
*   **CHOLAFIN:** Win Rate 62%, PnL +52%
*   **DLF:** Win Rate 60%, PnL +42%
*   **RECLTD:** Win Rate 63%, PnL +40%
*   **CANBK:** Win Rate 57%, PnL +38%
