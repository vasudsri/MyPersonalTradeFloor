import pandas as pd
import numpy as np
from hmmlearn.hmm import GaussianHMM
import logging
import os
import pickle

logger = logging.getLogger(__name__)

class MarketRegimeHMM:
    """
    Identifies hidden market states (regimes) using Gaussian Hidden Markov Models.
    Typically used to switch between Momentum and Mean Reversion strategies.
    """
    def __init__(self, n_regimes=3):
        self.n_regimes = n_regimes
        self.model = GaussianHMM(n_components=n_regimes, covariance_type="diag", n_iter=1000, random_state=42)
        self.model_path = "extensions/momentum_trading/data/hmm_regime_model.pkl"
        
    def prepare_features(self, df: pd.DataFrame):
        """Extracts returns and volatility range for HMM training/prediction."""
        df = df.copy()
        df['Returns'] = df['Close'].pct_change()
        df['Range'] = (df['High'] - df['Low']) / df['Close']
        df.dropna(inplace=True)
        return df[['Returns', 'Range']].values

    def train(self, df: pd.DataFrame):
        """Trains the HMM on historical data."""
        features = self.prepare_features(df)
        logger.info(f"Training HMM with {len(features)} samples...")
        self.model.fit(features)
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        logger.info(f"HMM model saved to {self.model_path}")

    def predict_regime(self, df: pd.DataFrame):
        """Predicts the current regime for the latest data point."""
        if not hasattr(self.model, "means_"):
            if os.path.exists(self.model_path):
                try:
                    with open(self.model_path, "rb") as f:
                        self.model = pickle.load(f)
                except Exception as e:
                    logger.warning("Failed loading HMM model, retraining: %s", e)
                    self.train(df)
            else:
                logger.info("HMM model not found. Training a new model from latest market data.")
                self.train(df)
        
        features = self.prepare_features(df)
        regimes = self.model.predict(features)
        current_regime = regimes[-1]
        
        # Map regime index to human-readable label based on means
        # State 0, 1, 2 doesn't always mean the same thing, we must inspect 'means_'
        means = self.model.means_
        # Sort indices by returns (first column of means)
        sorted_indices = np.argsort(means[:, 0]) # 0: lowest returns (Bearish), 2: highest (Bullish)
        
        mapping = {
            sorted_indices[0]: "BEARISH_VOLATILE",
            sorted_indices[1]: "SIDEWAYS_CHOPPY",
            sorted_indices[2]: "BULLISH_TRENDING"
        }
        
        return mapping.get(current_regime, "UNKNOWN")

    def get_strategy_recommendation(self, regime: str):
        """Decides which strategy to prioritize based on the regime."""
        recommendations = {
            "BULLISH_TRENDING": {
                "primary": "MOMENTUM",
                "secondary": "NONE",
                "risk_multiplier": 1.2,
                "rationale": "Strong trend detected. Momentum breakouts have high follow-through."
            },
            "SIDEWAYS_CHOPPY": {
                "primary": "MEAN_REVERSION",
                "secondary": "NONE",
                "risk_multiplier": 0.8,
                "rationale": "Range-bound market. Buy support, sell resistance. Avoid breakouts."
            },
            "BEARISH_VOLATILE": {
                "primary": "CASH",
                "secondary": "MEAN_REVERSION_SHORT",
                "risk_multiplier": 0.5,
                "rationale": "High panic/volatility. Capital preservation is priority. Look for extreme oversold bounces only."
            }
        }
        return recommendations.get(regime, {
            "primary": "MOMENTUM", "risk_multiplier": 1.0, "rationale": "Standard regime."
        })
