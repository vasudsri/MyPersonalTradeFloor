import json
import os
import logging
import yfinance as yf
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
                data = json.load(f)
                return data.get("shortlist", [])
        return []

    def fetch_data(self, symbol):
        try:
            return yf.download(symbol, period="1y", interval="1d", progress=False)
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def analyze_entry_conditions(self):
        if not self.shortlist:
            logger.info("Shortlist is empty. Run a Weekly scan to add candidates.")
            return

        logger.info(f"Analyzing {len(self.shortlist)} shortlisted stocks for Daily entry...")
        
        scanner = QullamaggieScanner(watchlist=self.shortlist, interval="1d")
        
        for symbol in self.shortlist:
            df = self.fetch_data(symbol)
            if df is None or df.empty: continue
            
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
            
            # Condition 4: Stochastic Pullback (Stoch < 30 indicates a potential dip to buy)
            is_stoch_pullback = curr['Stoch_D'] < 30
            
            # Condition 5: Trend Health (Long Stoch > 50)
            is_healthy_trend = curr['Stoch_D_Long'] > 50
            
            print(f"\n--- Analysis for {symbol} ---")
            print(f"   Price: {curr['Close']:.2f}, ADR: {adr:.1f}%, Stoch(9,3,3): {curr['Stoch_D']:.1f}")
            
            if is_breakout and vol_ratio > 1.2 and is_healthy_trend:
                signal = "🔥 BUY SIGNAL: BREAKOUT"
                if is_stoch_pullback: signal += " + STOCH PULLBACK"
                print(f"{signal}")
                print(f"   Action: Consider Entry. Volume: {vol_ratio:.1f}x. Stop at LOD: {curr['Low']:.2f}")
            elif is_hugging:
                print(f"⌛ STATUS: HUGGING EMAs (Getting Tight)")
                print(f"   Action: Watch for tomorrow's breakout. Stoch Long: {curr['Stoch_D_Long']:.1f}")
            elif is_stoch_pullback and is_healthy_trend:
                print(f"🎣 STATUS: PULLBACK IN UPTREND")
                print(f"   Action: Look for reversal candles near EMAs. Stoch: {curr['Stoch_D']:.1f}")
            else:
                print(f"💤 STATUS: NO SETUP")
                print(f"   Action: Wait for consolidation or breakout.")

if __name__ == "__main__":
    watcher = ActiveWatcher()
    watcher.analyze_entry_conditions()
