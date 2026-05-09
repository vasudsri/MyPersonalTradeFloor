import json
import os
import sys
import logging
import yfinance as yf
from datetime import datetime
import time

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions.momentum_trading.trading.portfolio import PortfolioManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def track_portfolio():
    """
    Fetches latest prices for all active positions and checks SL/Target.
    Updates the portfolio tracker.
    """
    manager = PortfolioManager()
    active_positions = manager.portfolio["active_positions"]
    
    if not active_positions:
        logger.info("No active positions to track.")
        return

    symbols = [p['symbol'] for p in active_positions]
    logger.info(f"Tracking {len(symbols)} active positions: {symbols}")
    
    try:
        # Fetch latest prices
        data = yf.download(symbols, period="1d", interval="1m", progress=False)
        
        if data.empty:
            logger.warning("No price data fetched.")
            return
            
        price_map = {}
        for symbol in symbols:
            # Handle both single and multi-stock dataframes
            if len(symbols) == 1:
                price_map[symbol] = float(data['Close'].iloc[-1])
            else:
                price_map[symbol] = float(data['Close'][symbol].iloc[-1])
        
        # Update portfolio
        manager.update_prices(price_map)
        logger.info("Portfolio updated successfully.")
        
    except Exception as e:
        logger.error(f"Error tracking portfolio: {e}")

if __name__ == "__main__":
    track_portfolio()
