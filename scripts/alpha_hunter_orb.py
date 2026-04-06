import pandas as pd
import numpy as np
import os
import sys
import glob
from datetime import datetime

# Setup paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

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

def run_alpha_hunter():
    print(f"--- Champion ORB Alpha Hunter: Scanning for New Champions ---")
    
    data_dir = "extensions/momentum_trading/data/fine"
    daily_path = os.path.join(data_dir, "NIFTY_UNIFIED.parquet")
    stock_files = glob.glob(os.path.join(data_dir, "*_5minute.parquet"))
    
    if not stock_files:
        print("No stock files found.")
        return

    print(f"Found {len(stock_files)} stocks to analyze.")
    
    # Load Daily Trend Filter
    df_daily_all = pd.read_parquet(daily_path)
    if 'Date' in df_daily_all.columns:
        df_daily_all['Date'] = pd.to_datetime(df_daily_all['Date'])
        df_daily_all.set_index('Date', inplace=True)
    df_daily_all = df_daily_all.sort_index()
    df_daily_all['EMA20'] = df_daily_all['Close'].ewm(span=20, adjust=False).mean()
    daily_trend = (df_daily_all['Close'] > df_daily_all['EMA20']).shift(1)

    all_results = []

    count = 0
    for stock_file in stock_files:
        symbol = os.path.basename(stock_file).replace("_5minute.parquet", "")
        count += 1
        if count % 10 == 0:
            print(f"Progress: Analyzed {count}/{len(stock_files)} stocks...")
        
        # Skip NIFTY unified if it's there
        if "NIFTY" in symbol: continue
        
        try:
            df = pd.read_parquet(stock_file)
            if 'Date' in df.columns: df.rename(columns={'Date': 'date'}, inplace=True)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.sort_index()
            df.columns = [c.lower() for c in df.columns]

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

                try:
                    orb_candle = day_data.between_time('09:15', '09:15').iloc[0]
                    orb_h, orb_l = orb_candle['high'], orb_candle['low']
                except: continue

                window = day_data.between_time('09:20', '15:25')
                in_pos, pos_type, entry_p, sl_p, max_p, min_p = False, None, 0, 0, 0, 0
                break_u, break_d = False, False

                for time, row in window.iterrows():
                    if not in_pos:
                        if time.time() > pd.to_datetime('10:30').time(): break
                        if row['close'] > orb_h: break_u = True
                        if row['close'] < orb_l: break_d = True

                        if break_u and is_bull_trend:
                            if row['stoch_k'] < 20 and row['stoch_k'] > row['stoch_d']:
                                in_pos, pos_type, entry_p, sl_p = True, 'LONG', row['close'], orb_l
                                max_p = entry_p
                        elif break_d and not is_bull_trend:
                            if row['stoch_k'] > 80 and row['stoch_k'] < row['stoch_d']:
                                in_pos, pos_type, entry_p, sl_p = True, 'SHORT', row['close'], orb_h
                                min_p = entry_p

                    elif in_pos:
                        if pos_type == 'LONG':
                            max_p = max(max_p, row['high'])
                            trail = max_p - (1.8 * row['atr'])
                            curr_sl = max(sl_p, trail)
                            if row['low'] <= curr_sl:
                                trades.append((curr_sl - entry_p)/entry_p * 100)
                                in_pos = False; break
                            elif time.time() >= pd.to_datetime('15:20').time():
                                trades.append((row['close'] - entry_p)/entry_p * 100)
                                in_pos = False; break
                        else: # SHORT
                            min_p = min(min_p, row['low'])
                            trail = min_p + (1.8 * row['atr'])
                            curr_sl = min(sl_p, trail)
                            if row['high'] >= curr_sl:
                                trades.append((entry_p - curr_sl)/entry_p * 100)
                                in_pos = False; break
                            elif time.time() >= pd.to_datetime('15:20').time():
                                trades.append((entry_p - row['close'])/entry_p * 100)
                                in_pos = False; break
            
            if trades:
                win_rate = len([t for t in trades if t > 0]) / len(trades)
                total_pnl = sum(trades)
                all_results.append({
                    "Symbol": symbol,
                    "Total_PnL": round(total_pnl, 2),
                    "Win_Rate": round(win_rate * 100, 2),
                    "Trades": len(trades),
                    "Avg_PnL": round(total_pnl / len(trades), 2)
                })
                # print(f"Analyzed {symbol}: PnL {total_pnl:.2f}% | WR {win_rate*100:.1f}%")

        except Exception as e:
            # print(f"Error analyzing {symbol}: {e}")
            continue

    if not all_results:
        print("No results found.")
        return

    results_df = pd.DataFrame(all_results)
    results_df = results_df.sort_values(by="Total_PnL", ascending=False)
    
    # Identify Champions (Win Rate > 55% AND Total PnL > 35%)
    champions = results_df[(results_df['Win_Rate'] > 55) & (results_df['Total_PnL'] > 35)]
    
    print("\n" + "="*60)
    print(f"   NEW ALPHA CHAMPIONS IDENTIFIED ({len(champions)} STOCKS)")
    print("="*60)
    print(champions.head(20).to_string(index=False))
    print("="*60)
    
    # Save to JSON for the system to use
    champions_list = champions['Symbol'].tolist()
    with open("extensions/momentum_trading/configs/champion_orb_v1.json", "w") as f:
        import json
        json.dump({"symbols": champions_list}, f, indent=4)
    print(f"\nUpdated Champion Watchlist saved to extensions/momentum_trading/configs/champion_orb_v1.json")

if __name__ == "__main__":
    run_alpha_hunter()
