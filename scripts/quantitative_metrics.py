import pandas as pd
import numpy as np
import os

def run_quantitative_analysis(log_path):
    if not os.path.exists(log_path):
        print(f"Error: {log_path} not found.")
        return

    df = pd.read_csv(log_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 1. Basic Stats
    total_trades = len(df)
    winners = df[df['PnL_Pct'] > 0]
    losers = df[df['PnL_Pct'] <= 0]
    win_rate = len(winners) / total_trades if total_trades > 0 else 0
    
    avg_win = winners['PnL_Pct'].mean() if not winners.empty else 0
    avg_loss = abs(losers['PnL_Pct'].mean()) if not losers.empty else 0
    
    # 2. Performance Ratios
    # Sharpe Ratio Calculation
    # We group by date to get daily strategy returns (sum of all stocks traded that day)
    daily_returns = df.groupby('Date')['PnL_Pct'].sum()
    risk_free_rate_annual = 0.07
    risk_free_rate_daily = risk_free_rate_annual / 252 
    excess_returns = daily_returns - risk_free_rate_daily
    
    if len(daily_returns) > 1 and daily_returns.std() != 0:
        sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
    else:
        sharpe_ratio = 0.0
    
    # Expectancy: (Win% * AvgWin) - (Loss% * AvgLoss)
    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
    
    # Profit Factor
    gross_profits = winners['PnL_Pct'].sum()
    gross_losses = abs(losers['PnL_Pct'].sum())
    profit_factor = gross_profits / gross_losses if gross_losses != 0 else float('inf')
    
    # Max Drawdown (Aggregate Strategy Level)
    # We sort by date and calculate cumulative PnL
    strategy_curve = df.sort_values('Date').groupby('Date')['PnL_Pct'].sum().cumsum()
    peak = strategy_curve.cummax()
    drawdown = strategy_curve - peak
    max_dd = drawdown.min()

    # 3. Trade Distribution Analysis
    # Convert times to timedelta for duration calculation
    avg_hold_time_winners = (pd.to_datetime(winners['Exit_Time'], format='%H:%M:%S') - 
                             pd.to_datetime(winners['Entry_Time'], format='%H:%M:%S')).mean() if not winners.empty else "N/A"
    avg_hold_time_losers = (pd.to_datetime(losers['Exit_Time'], format='%H:%M:%S') - 
                            pd.to_datetime(losers['Entry_Time'], format='%H:%M:%S')).mean() if not losers.empty else "N/A"

    print("\n" + "="*50)
    print("   STRATEGY-LEVEL QUANTITATIVE METRICS")
    print("="*50)
    print(f"Total Trades:         {total_trades}")
    print(f"Win Rate:             {win_rate*100:.2f}%")
    print(f"Avg Win:              {avg_win:+.2f}%")
    print(f"Avg Loss:             {avg_loss:+.2f}%")
    print(f"Win/Loss Ratio:       {avg_win/avg_loss if avg_loss != 0 else 0:.2f}")
    print("-" * 30)
    print(f"Sharpe Ratio:         {sharpe_ratio:.2f}")
    print(f"Expectancy (per tr):  {expectancy:+.2f}%")
    print(f"Profit Factor:        {profit_factor:.2f}")
    print(f"Max Strategy DD:      {max_dd:.2f}%")
    print("-" * 30)
    print(f"Avg Hold (Winners):   {avg_hold_time_winners}")
    print(f"Avg Hold (Losers):    {avg_hold_time_losers}")
    print("="*50)

    # Distribution Check
    print("\nTRADE DISTRIBUTION (PnL %):")
    bins = [-np.inf, -2, -1, -0.5, 0, 0.5, 1, 2, np.inf]
    labels = ['< -2%', '-2% to -1%', '-1% to -0.5%', '-0.5% to 0%', '0% to 0.5%', '0.5% to 1%', '1% to 2%', '> 2%']
    dist = pd.cut(df['PnL_Pct'], bins=bins, labels=labels).value_counts().sort_index()
    for label, count in dist.items():
        print(f"   {label:15}: {count} trades ({(count/total_trades)*100:.1f}%)")
    print("="*50 + "\n")

if __name__ == "__main__":
    log_file = "Momentum-Trader-Private/extensions/momentum_trading/data/orb_stocks_backtest_log.csv"
    run_quantitative_analysis(log_file)
