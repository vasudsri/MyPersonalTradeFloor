import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_atr(df, period=14):
    h_l = df['high'] - df['low']
    h_pc = abs(df['high'] - df['close'].shift(1))
    l_pc = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calculate_stochastic(df, k_period=9, d_period=3, slowing=3):
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    fast_k = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['stoch_k'] = fast_k.rolling(window=slowing).mean()
    df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
    return df

def backtest_orb_strategy(stock_files, daily_path):
    print(f"Loading daily data for trend filter: {daily_path}")
    df_daily_all = pd.read_parquet(daily_path)
    if 'Date' in df_daily_all.columns:
        df_daily_all['Date'] = pd.to_datetime(df_daily_all['Date'])
        df_daily_all.set_index('Date', inplace=True)
    df_daily_all = df_daily_all.sort_index()
    df_daily_all['EMA20'] = df_daily_all['Close'].ewm(span=20, adjust=False).mean()
    daily_trend = (df_daily_all['Close'] > df_daily_all['EMA20']).shift(1)

    all_stock_trades = []

    for stock_file in stock_files:
        symbol = os.path.basename(stock_file).replace("_5minute.parquet", "")
        print(f"\nProcessing Stock: {symbol}")
        
        if not os.path.exists(stock_file):
            print(f"File {stock_file} not found. Skipping.")
            continue
            
        # Read parquet instead of csv
        df = pd.read_parquet(stock_file)
        
        # Ensure 'date' column is lowercase (from our converter)
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
            
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()

        # Lowercase column names for the rest of the logic
        df.columns = [c.lower() for c in df.columns]

        # Prepare intraday indicators
        df['atr'] = calculate_atr(df)
        df = calculate_stochastic(df)
        
        trades = []
        all_days = df.index.normalize().unique()
        
        for day in all_days:
            day_data = df[df.index.normalize() == day].copy()
            if len(day_data) < 20: continue
            
            try:
                is_bull_trend = daily_trend.loc[day]
                if pd.isna(is_bull_trend): continue
            except: continue

            # 1. Define Opening Range (09:15 candle)
            try:
                orb_candle = day_data.between_time('09:15', '09:15').iloc[0]
                orb_h, orb_l = orb_candle['high'], orb_candle['low']
            except: continue

            # 2. Trading Window (09:20 - 10:30 for entry)
            window = day_data.between_time('09:20', '15:25')
            
            in_pos = False
            pos_type = None
            entry_p, entry_time, sl_p, max_p, min_p = 0, None, 0, 0, 0
            break_u, break_d = False, False

            for time, row in window.iterrows():
                if not in_pos:
                    if time.time() > pd.to_datetime('10:30').time(): break
                    
                    if row['close'] > orb_h: break_u = True
                    if row['close'] < orb_l: break_d = True

                    # LONG Entry
                    if break_u and is_bull_trend:
                        if row['stoch_k'] < 20 and row['stoch_k'] > row['stoch_d']:
                            in_pos, pos_type, entry_p, entry_time = True, 'LONG', row['close'], time
                            sl_p = orb_l
                            max_p = entry_p
                    
                    # SHORT Entry
                    elif break_d and not is_bull_trend:
                        if row['stoch_k'] > 80 and row['stoch_k'] < row['stoch_d']:
                            in_pos, pos_type, entry_p, entry_time = True, 'SHORT', row['close'], time
                            sl_p = orb_h
                            min_p = entry_p

                elif in_pos:
                    if pos_type == 'LONG':
                        max_p = max(max_p, row['high'])
                        trail = max_p - (1.8 * row['atr'])
                        curr_sl = max(sl_p, trail)
                        
                        if row['low'] <= curr_sl:
                            exit_p = curr_sl
                            pnl = exit_p - entry_p
                            trades.append({"Symbol": symbol, "Date": day.date(), "Type": "LONG", "Entry_Time": entry_time.time(), "Exit_Time": time.time(), "Entry_P": entry_p, "Exit_P": exit_p, "PnL_Pct": round((pnl/entry_p)*100, 2), "Reason": "SL/Trail"})
                            in_pos = False; break
                        elif time.time() >= pd.to_datetime('15:20').time():
                            exit_p = row['close']
                            pnl = exit_p - entry_p
                            trades.append({"Symbol": symbol, "Date": day.date(), "Type": "LONG", "Entry_Time": entry_time.time(), "Exit_Time": time.time(), "Entry_P": entry_p, "Exit_P": exit_p, "PnL_Pct": round((pnl/entry_p)*100, 2), "Reason": "EOD"})
                            in_pos = False; break
                    
                    else: # SHORT
                        min_p = min(min_p, row['low'])
                        trail = min_p + (1.8 * row['atr'])
                        curr_sl = min(sl_p, trail)
                        
                        if row['high'] >= curr_sl:
                            exit_p = curr_sl
                            pnl = entry_p - exit_p
                            trades.append({"Symbol": symbol, "Date": day.date(), "Type": "SHORT", "Entry_Time": entry_time.time(), "Exit_Time": time.time(), "Entry_P": entry_p, "Exit_P": exit_p, "PnL_Pct": round((pnl/entry_p)*100, 2), "Reason": "SL/Trail"})
                            in_pos = False; break
                        elif time.time() >= pd.to_datetime('15:20').time():
                            exit_p = row['close']
                            pnl = entry_p - exit_p
                            trades.append({"Symbol": symbol, "Date": day.date(), "Type": "SHORT", "Entry_Time": entry_time.time(), "Exit_Time": time.time(), "Entry_P": entry_p, "Exit_P": exit_p, "PnL_Pct": round((pnl/entry_p)*100, 2), "Reason": "EOD"})
                            in_pos = False; break
        
        all_stock_trades.extend(trades)

    if not all_stock_trades:
        print("No trades triggered for selected stocks.")
        return

    results = pd.DataFrame(all_stock_trades)
    log_dir = "Momentum-Trader-Private/extensions/momentum_trading/data"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "orb_stocks_backtest_log.csv")
    results.to_csv(log_path, index=False)
    print(f"\nDetailed trade log saved to: {log_path}")

    # Annual PnL Calculation
    results['Year'] = pd.to_datetime(results['Date']).dt.year
    annual_pnl = results.groupby('Year')['PnL_Pct'].sum()

    print("\n" + "="*40)
    print(f"   CHAMPION ORB STOCK AGGREGATE RESULTS")
    print("="*40)
    print(f"Total Trades: {len(results)}")
    print(f"Win Rate:     {(len(results[results['PnL_Pct'] > 0]) / len(results)) * 100:.2f}%")
    print(f"Total PnL %:  {results['PnL_Pct'].sum():.2f}%")
    print(f"Avg PnL %:    {results['PnL_Pct'].mean():.2f}%")
    print(f"Max Drawdown: {results['PnL_Pct'].min():.2f}%")
    print("\nANNUAL PnL BREAKDOWN (Aggregated):")
    for year, pnl in annual_pnl.items():
        print(f"   {year}: {pnl:+.2f}%")
    print("\nPER STOCK BREAKDOWN:")
    stock_pnl = results.groupby('Symbol')['PnL_Pct'].sum()
    for stock, pnl in stock_pnl.items():
        print(f"   {stock}: {pnl:+.2f}%")
    print("="*40)

if __name__ == "__main__":
    stocks = [
        "extensions/momentum_trading/data/fine/ADANIENT_5minute.parquet",
        "extensions/momentum_trading/data/fine/CHOLAFIN_5minute.parquet",
        "extensions/momentum_trading/data/fine/DLF_5minute.parquet",
        "extensions/momentum_trading/data/fine/RECLTD_5minute.parquet",
        "extensions/momentum_trading/data/fine/CANBK_5minute.parquet"
    ]
    backtest_orb_strategy(
        stocks,
        "extensions/momentum_trading/data/fine/NIFTY_UNIFIED.parquet"
    )
