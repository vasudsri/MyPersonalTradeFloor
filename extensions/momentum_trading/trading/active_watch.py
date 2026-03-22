import json
import os
import logging
from extensions.momentum_trading.trading.scanner import QullamaggieScanner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_PATH = "extensions/momentum_trading/configs/active_watch.json"

class ActiveWatcher:
    """
    Monitors a shortlist of Weekly picks for the exact DAILY entry point.
    """
    def __init__(self):
        self.shortlist = self._load_shortlist()

    def _load_shortlist(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f).get("shortlist", [])
        return []

    def analyze_entry_conditions(self):
        if not self.shortlist:
            logger.info("Shortlist is empty. Run a Weekly scan to add candidates.")
            return

        logger.info(f"Analyzing {len(self.shortlist)} shortlisted stocks for Daily entry...")
        
        # Use Daily interval
        scanner = QullamaggieScanner(watchlist=self.shortlist, interval="1d")
        
        for symbol in self.shortlist:
            df = scanner.fetch_data(symbol)
            if df.empty: continue
            df = scanner.add_indicators(df)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            adr = scanner.calculate_adr(df)
            
            # Condition 1: EMA Hugging (Price is tight near 10 or 20 EMA)
            dist_ema10 = abs(curr['Close'] - curr['EMA10']) / curr['EMA10'] * 100
            dist_ema20 = abs(curr['Close'] - curr['EMA20']) / curr['EMA20'] * 100
            is_hugging = dist_ema10 < 1.5 or dist_ema20 < 1.5
            
            # Condition 2: Volume Surge (Current volume > 20-day avg)
            vol_ratio = curr['Volume'] / curr['VolAvg20']
            
            # Condition 3: Price Breakout (Breaking above yesterday's high)
            is_breakout = curr['Close'] > prev['High']
            
            print(f"\n--- Analysis for {symbol} ---")
            if is_breakout and vol_ratio > 1.2:
                print(f"🔥 SIGNAL: DAILY BREAKOUT DETECTED!")
                print(f"   Action: Consider Entry. Volume: {vol_ratio:.1f}x. Stop at LOD: {curr['Low']:.2f}")
            elif is_hugging:
                print(f"⌛ STATUS: HUGGING EMAs (Getting Tight)")
                print(f"   Action: Add to Alert. Volatility is contracting near EMAs.")
            else:
                print(f"💤 STATUS: CHOPPY / NO SIGNAL")
                print(f"   Action: Wait for price to tighten or break yesterday's high.")

if __name__ == "__main__":
    watcher = ActiveWatcher()
    watcher.analyze_entry_conditions()
