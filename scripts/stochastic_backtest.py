import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt

# Add the project root to sys.path to import the Kalman Filter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions.momentum_trading.trading.stochastic import KalmanTrendFilter

def calculate_atr(df, period=14):
    h_l = df['High'] - df['Low']
    h_pc = abs(df['High'] - df['Close'].shift(1))
    l_pc = abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def run_stochastic_comparison(file_path, start_year=2015, end_year=2025):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    # 1. Load Data
    df = pd.read_parquet(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    df = df.sort_index()
    
    # 2. Add Traditional Indicators
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['ATR14'] = calculate_atr(df)
    
    # 3. Add Kalman Filter (Stochastic)
    # Tuning: lower process_variance = smoother/more lag, higher = more reactive
    kf = KalmanTrendFilter(process_variance=1e-4, estimated_measurement_variance=1e-2)
    df['Kalman_Trend'] = kf.filter(df['Close'])
    
    # 4. Filter for backtest period
    df = df[(df.index.year >= start_year) & (df.index.year <= end_year)]
    print(f"Comparing EMA20 vs Kalman Filter from {start_year} to {end_year}...")

    # Strategy 1: Traditional (EMA20 Exit)
    # Strategy 2: Stochastic (Kalman Exit)
    
    results = {
        "EMA20": backtest_logic(df, 'EMA20'),
        "Kalman": backtest_logic(df, 'Kalman_Trend')
    }

    print_report(results, start_year, end_year)
    plot_comparison(df.tail(200)) # Plot last 200 days for visual check

def backtest_logic(df, trend_col):
    trades = []
    in_pos = False
    entry_p, entry_date, sl_p, max_p = 0, None, 0, 0
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        curr_date = df.index[i]
        
        near_trend = (abs(row['Close'] - row[trend_col]) / row[trend_col] < 0.02)

        if not in_pos:
            # ENTRY: Breakout of yesterday's high while near trend
            if near_trend and (row['Close'] > prev_row['High']):
                in_pos = True
                entry_p = row['Close']
                entry_date = curr_date
                sl_p = row['Low']
                max_p = entry_p
                
        elif in_pos:
            max_p = max(max_p, row['High'])
            # Trailing Stop: 1.8x ATR
            trail_sl = max_p - (1.8 * row['ATR14'])
            sl_p = max(sl_p, trail_sl)
            
            # EXIT: Hit SL or Close below Trend
            if row['Low'] <= sl_p or row['Close'] < row[trend_col]:
                exit_p = sl_p if row['Low'] <= sl_p else row['Close']
                pnl_pct = ((exit_p - entry_p) / entry_p) * 100
                trades.append(pnl_pct)
                in_pos = False
                
    return trades

def print_report(results, start_year, end_year):
    print("\n" + "="*50)
    print(f"   STOCHASTIC VS TRADITIONAL BACKTEST ({start_year}-{end_year})")
    print("="*50)
    for name, trades in results.items():
        if not trades:
            print(f"{name}: No trades.")
            continue
        pnl = np.array(trades)
        pos_pnl = pnl[pnl > 0]
        neg_pnl = pnl[pnl < 0]
        
        win_rate = (len(pos_pnl) / len(pnl)) * 100
        profit_factor = abs(pos_pnl.sum() / neg_pnl.sum()) if neg_pnl.sum() != 0 else float('inf')
        
        print(f"[{name} Strategy]")
        print(f"  Total Trades: {len(pnl)}")
        print(f"  Win Rate:     {win_rate:.2f}%")
        print(f"  Total PnL %:  {pnl.sum():.2f}%")
        print(f"  Avg PnL %:    {pnl.mean():.2f}%")
        print(f"  Profit Factor: {profit_factor:.2f}")
        print("-" * 20)

def plot_comparison(df):
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['Close'], label='Price', color='black', alpha=0.5)
    plt.plot(df.index, df['EMA20'], label='EMA20 (Laggy)', color='red', linestyle='--')
    plt.plot(df.index, df['Kalman_Trend'], label='Kalman (Adaptive)', color='blue')
    plt.title('EMA20 vs Kalman Filter Trend Detection')
    plt.legend()
    plt.grid(True, alpha=0.3)
    output_path = "Momentum-Trader-Private/extensions/momentum_trading/data/stochastic_comparison.png"
    plt.savefig(output_path)
    print(f"\nComparison plot saved to: {output_path}")

if __name__ == "__main__":
    data_path = "Momentum-Trader-Private/extensions/momentum_trading/data/fine/NIFTY_UNIFIED.parquet"
    run_stochastic_comparison(data_path)
