import requests
import pandas as pd
import json
import os
import logging
import io
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_PATH = "extensions/momentum_trading/configs/nifty200.json"
NSE_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"

def fetch_nifty_200() -> List[str]:
    """Fetches the latest NIFTY 200 symbols from NSE Indices."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.info(f"Downloading latest NIFTY 200 list from {NSE_URL}...")
        response = requests.get(NSE_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Read CSV from memory
        df = pd.read_csv(io.StringIO(response.text))
        
        if 'Symbol' not in df.columns:
            logger.error("CSV downloaded but 'Symbol' column not found.")
            return []
            
        symbols = [f"{sym}.NS" for sym in df['Symbol'].tolist()]
        logger.info(f"Successfully fetched {len(symbols)} symbols.")
        return symbols
        
    except Exception as e:
        logger.error(f"Failed to fetch NIFTY 200: {e}")
        return []

def update_watchlist():
    """Main function to update the local configuration file."""
    symbols = fetch_nifty_200()
    
    if not symbols:
        logger.warning("No symbols fetched. Watchlist update aborted.")
        return
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    
    data = {
        "index": "NIFTY 200",
        "last_updated": pd.Timestamp.now().isoformat(),
        "symbols": symbols
    }
    
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)
        
    logger.info(f"Updated {CONFIG_PATH} with {len(symbols)} symbols.")

if __name__ == "__main__":
    update_watchlist()
