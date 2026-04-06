import pandas as pd
import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from extensions.momentum_trading.trading.regime import MarketRegimeHMM

def train_hmm():
    data_path = "Momentum-Trader-Private/extensions/momentum_trading/data/fine/NIFTY_UNIFIED.parquet"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    hmm = MarketRegimeHMM(n_regimes=3)
    hmm.train(df)
    
    # Verify by predicting latest
    regime = hmm.predict_regime(df)
    recommendation = hmm.get_strategy_recommendation(regime)
    
    print("\n" + "="*40)
    print(f"   HMM TRAINING COMPLETE")
    print("="*40)
    print(f"Current Market Regime: {regime}")
    print(f"Primary Strategy:      {recommendation['primary']}")
    print(f"Risk Multiplier:       {recommendation['risk_multiplier']}x")
    print(f"Rationale:             {recommendation['rationale']}")
    print("="*40)

if __name__ == "__main__":
    train_hmm()
