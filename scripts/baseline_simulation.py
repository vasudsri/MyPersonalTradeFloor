import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_adr(df, period=20):
    daily_range = (df['High'] - df['Low']) / df['Low'] * 100
    return daily_range.rolling(period).mean()

def calculate_atr(df, period=14):
    h_l = df['High'] - df['Low']
    h_pc = abs(df['High'] - df['Close'].shift(1))
    l_pc = abs(df['Low'] - df['Close'].shift(1))
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def add_indicators(df):
    df = df.copy()
    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['ADR20'] = calculate_adr(df)
    df['ATR14'] = calculate_atr(df)
    return df

def backtest_index_strategy(file_path, start_year=2015, end_year=2025):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    # 1. Load Data
    df = pd.read_parquet(file_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    df = df.sort_index()
    
    # 2. Add Indicators
    df = add_indicators(df)
    
    # 3. Filter for backtest period
    df = df[(df.index.year >= start_year) & (df.index.year <= end_year)]
    print(f"Backtesting Qullamaggie Index Strategy from {start_year} to {end_year}...")

    trades = []
    in_pos = False
    entry_p, entry_date, sl_p, max_p, entry_vol = 0, None, 0, 0, 0
    
    # Simulation
    for i in range(60, len(df)):
        curr_date = df.index[i]
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        near_ema = (abs(row['Close'] - row['EMA10']) / row['EMA10'] < 0.02) or \
                   (abs(row['Close'] - row['EMA20']) / row['EMA20'] < 0.02)

        if not in_pos:
            # ENTRY: Breakout of yesterday's high while near EMA
            if near_ema and (row['Close'] > prev_row['High']):
                in_pos = True
                entry_p = row['Close']
                entry_date = curr_date
                entry_vol = row['Volume']
                sl_p = row['Low']
                max_p = entry_p
                
        elif in_pos:
            max_p = max(max_p, row['High'])
            # Trailing Stop: 1.8x ATR
            trail_sl = max_p - (1.8 * row['ATR14'])
            sl_p = max(sl_p, trail_sl)
            
            # EXIT: Hit SL or Close below EMA20
            if row['Low'] <= sl_p or row['Close'] < row['EMA20']:
                exit_p = sl_p if row['Low'] <= sl_p else row['Close']
                exit_vol = row['Volume']
                pnl = exit_p - entry_p
                pnl_pct = (pnl / entry_p) * 100
                trades.append({
                    "Entry_Date": entry_date,
                    "Exit_Date": curr_date,
                    "Entry_Price": entry_p,
                    "Exit_Price": exit_p,
                    "Entry_Volume": entry_vol,
                    "Exit_Volume": exit_vol,
                    "PnL_Points": round(pnl, 2),
                    "PnL_Pct": round(pnl_pct, 2)
                })
                in_pos = False

    # 5. Reporting and Logging
    if not trades:
        print("No trades triggered.")
        return

    results = pd.DataFrame(trades)
    
    # Ensure directory exists
    log_dir = "Momentum-Trader-Private/extensions/momentum_trading/data"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "index_backtest_log.csv")
    results.to_csv(log_path, index=False)
    print(f"Detailed trade log saved to: {log_path}")

    # Annual PnL Calculation
    results['Year'] = results['Entry_Date'].dt.year
    annual_pnl = results.groupby('Year')['PnL_Pct'].sum()

    print("\n" + "="*40)
    print(f"   INDEX BACKTEST RESULTS ({start_year}-{end_year})")
    print("="*40)
    print(f"Total Trades: {len(results)}")
    print(f"Win Rate:     {(len(results[results['PnL_Pct'] > 0]) / len(results)) * 100:.2f}%")
    print(f"Total PnL %:  {results['PnL_Pct'].sum():.2f}%")
    print(f"Avg PnL %:    {results['PnL_Pct'].mean():.2f}%")
    print(f"Max Drawdown: {results['PnL_Pct'].min():.2f}%")
    print("\nANNUAL PnL BREAKDOWN:")
    for year, pnl in annual_pnl.items():
        print(f"   {year}: {pnl:+.2f}%")
    print("="*40)

if __name__ == "__main__":
    backtest_index_strategy("OpenJarvis/src/openjarvis/data/refine/NIFTY_UNIFIED.parquet")
