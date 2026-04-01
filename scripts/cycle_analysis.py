import pandas as pd
import numpy as np
import os

def run_cycle_analysis(log_path):
    if not os.path.exists(log_path):
        print(f"Error: {log_path} not found.")
        return

    df = pd.read_csv(log_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')

    # Define Market Regimes based on NIFTY Index history
    # Bull: 2017, 2021, 2023, 2024
    # Bear/Sideways: 2015, 2016, 2018, 2019, 2022
    # Volatile/Recovery: 2020
    regimes = {
        "Bull": [2017, 2021, 2023, 2024],
        "Bear/Sideways": [2015, 2016, 2018, 2019, 2022],
        "Crisis/Recovery": [2020]
    }

    def get_regime(year):
        for name, years in regimes.items():
            if year in years:
                return name
        return "Unknown"

    df['Regime'] = df['Date'].dt.year.apply(get_regime)

    print("\n" + "="*50)
    print("   MARKET CYCLE PERFORMANCE ANALYSIS")
    print("="*50)

    summary = []
    for regime in regimes.keys():
        regime_df = df[df['Regime'] == regime]
        if regime_df.empty: continue
        
        win_rate = (len(regime_df[regime_df['PnL_Pct'] > 0]) / len(regime_df)) * 100
        total_pnl = regime_df['PnL_Pct'].sum()
        avg_pnl = regime_df['PnL_Pct'].mean()
        
        summary.append({
            "Regime": regime,
            "Trades": len(regime_df),
            "Win_Rate": f"{win_rate:.2f}%",
            "Total_PnL": f"{total_pnl:+.2f}%",
            "Avg_PnL": f"{avg_pnl:+.2f}%"
        })

    print(pd.DataFrame(summary).to_string(index=False))

    # --- Drawdown & Time to Recovery ---
    # We calculate cumulative PnL to find drawdown
    df['Cum_PnL'] = df['PnL_Pct'].cumsum()
    df['Peak'] = df['Cum_PnL'].cummax()
    df['Drawdown'] = df['Cum_PnL'] - df['Peak']
    
    max_dd = df['Drawdown'].min()
    
    # Find the duration of the longest drawdown
    # We look for periods where Drawdown < 0
    df['Is_DD'] = df['Drawdown'] < 0
    # Group consecutive True values
    df['DD_Group'] = (df['Is_DD'] != df['Is_DD'].shift()).cumsum()
    dd_groups = df[df['Is_DD']].groupby('DD_Group')
    
    max_recovery_days = 0
    recovery_period = (None, None)
    
    for _, group in dd_groups:
        duration = (group['Date'].max() - group['Date'].min()).days
        if duration > max_recovery_days:
            max_recovery_days = duration
            recovery_period = (group['Date'].min().date(), group['Date'].max().date())

    print("\n" + "="*50)
    print("   RISK & RECOVERY METRICS")
    print("="*50)
    print(f"Max Strategy Drawdown: {max_dd:.2f}%")
    print(f"Longest Recovery Time: {max_recovery_days} days")
    if recovery_period[0]:
        print(f"Recovery Window:       {recovery_period[0]} to {recovery_period[1]}")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_cycle_analysis("Momentum-Trader-Private/extensions/momentum_trading/data/orb_stocks_backtest_log.csv")
