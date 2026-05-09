import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class KalmanTrendFilter:
    """
    A 1D Kalman Filter to track the underlying trend of a price series,
    dynamically filtering out market noise. It acts as an adaptive moving average.
    """
    def __init__(self, process_variance=1e-5, estimated_measurement_variance=1e-3):
        """
        process_variance: How fast we assume the 'true' trend can change.
        estimated_measurement_variance: How noisy we think the observations (prices) are.
        """
        self.process_variance = process_variance
        self.estimated_measurement_variance = estimated_measurement_variance
        
    def filter(self, prices: pd.Series) -> pd.Series:
        """
        Applies the Kalman Filter to a series of prices.
        Returns a pandas Series of the smoothed trend estimates.
        """
        n_iter = len(prices)
        sz = (n_iter,)
        
        # Allocate space for estimates
        posteriors = np.zeros(sz)
        posterior_error = np.zeros(sz)
        
        # Initial guesses
        if n_iter == 0:
            return pd.Series(dtype=float)
            
        posteriors[0] = prices.iloc[0]
        posterior_error[0] = 1.0
        
        for i in range(1, n_iter):
            # Time update (Predict)
            prior = posteriors[i-1]
            prior_error = posterior_error[i-1] + self.process_variance
            
            # Measurement update (Correct)
            kalman_gain = prior_error / (prior_error + self.estimated_measurement_variance)
            posteriors[i] = prior + kalman_gain * (prices.iloc[i] - prior)
            posterior_error[i] = (1 - kalman_gain) * prior_error
            
        return pd.Series(posteriors, index=prices.index)
