import yfinance as yf
import pandas as pd
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UniverseGenerator:
    """
    Generates dual watchlists:
    1. Dynamic Universe: NIFTY 500 filtered for High ADR (Qullamaggie focus).
    2. Comprehensive Universe: All NSE Equities filtered for basic liquidity (Fundamental focus).
    """
    
    NIFTY_500_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    NSE_ALL_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    
    CONFIG_DIR = "Momentum-Trader-Private/extensions/momentum_trading/configs"

    def __init__(self):
        self.min_price = 50.0
        self.min_volume = 100000
        self.min_adr = 4.0 

    def get_tickers(self, url, series_filter=None):
        try:
            logger.info(f"Downloading tickers from {url}...")
            df = pd.read_csv(url)
            # Remove leading/trailing spaces from column names
            df.columns = df.columns.str.strip()
            
            if series_filter:
                # Ensure we match the series exactly
                series_col = 'SERIES' if 'SERIES' in df.columns else 'Series'
                df = df[df[series_col].str.strip() == series_filter.strip()]
            
            symbol_col = 'Symbol' if 'Symbol' in df.columns else 'SYMBOL'
            tickers = [f"{str(s).strip()}.NS" for s in df[symbol_col].tolist()]
            return list(set(tickers)) # Unique list
        except Exception as e:
            logger.error(f"Failed to fetch from {url}: {e}")
            return []

    def calculate_metrics(self, tickers, name="Universe"):
        if not tickers:
            logger.warning(f"No tickers provided for {name}")
            return pd.DataFrame()

        logger.info(f"Calculating metrics for {name} ({len(tickers)} symbols)...")
        chunk_size = 50
        all_metrics = []
        
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i+chunk_size]
            try:
                data = yf.download(chunk, period="150d", interval="1d", progress=False, group_by='ticker')
                
                for symbol in chunk:
                    try:
                        # Handle multi-index columns from yfinance
                        df = data[symbol] if len(chunk) > 1 else data
                        df = df.dropna()
                        if len(df) < 63: continue
                        
                        last_price = float(df['Close'].iloc[-1])
                        avg_vol = float(df['Volume'].tail(20).mean())
                        
                        # Basic Liquidity Filter
                        if last_price < self.min_price or avg_vol < self.min_volume: continue

                        daily_range = (df['High'] - df['Low']) / df['Low'] * 100
                        adr = daily_range.tail(20).mean()
                        momentum_3m = (df['Close'].iloc[-1] / df['Close'].iloc[-63] - 1) * 100

                        all_metrics.append({
                            "symbol": symbol,
                            "price": round(last_price, 2),
                            "avg_volume": int(avg_vol),
                            "adr": round(adr, 2),
                            "momentum_3m": round(momentum_3m, 2)
                        })
                    except Exception: continue
            except Exception as e:
                logger.error(f"Chunk download failed: {e}")
                continue
                
        return pd.DataFrame(all_metrics)

    def enrich_fundamentals(self, df):
        """Fetches fundamentals for potential candidates."""
        if df.empty: return df
        logger.info(f"Enriching fundamentals for {len(df)} liquid NSE candidates...")
        enriched = []
        # Limit to top 300 liquid stocks to keep it reasonable
        df_limited = df.head(300) 
        
        for _, row in df_limited.iterrows():
            try:
                t = yf.Ticker(row['symbol'])
                info = t.info
                row_dict = row.to_dict()
                row_dict['market_cap'] = info.get('marketCap', 0)
                row_dict['roe'] = info.get('returnOnEquity', 0)
                enriched.append(row_dict)
            except Exception:
                enriched.append(row.to_dict())
        return pd.DataFrame(enriched)

    def run(self):
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        
        # 1. GENERATE DYNAMIC UNIVERSE (NIFTY 500)
        n500_tickers = self.get_tickers(self.NIFTY_500_URL)
        n500_metrics = self.calculate_metrics(n500_tickers, "NIFTY 500")
        
        if not n500_metrics.empty:
            high_adr_n500 = n500_metrics[n500_metrics['adr'] >= self.min_adr].copy()
            with open(os.path.join(self.CONFIG_DIR, "dynamic_universe.json"), "w") as f:
                json.dump({
                    "updated_at": datetime.now().isoformat(),
                    "symbols": high_adr_n500['symbol'].tolist(),
                    "metadata": high_adr_n500.to_dict(orient='records')
                }, f, indent=4)
            logger.info(f"Saved {len(high_adr_n500)} High-ADR NIFTY 500 stocks.")

        # 2. GENERATE COMPREHENSIVE UNIVERSE (ALL NSE)
        all_tickers = self.get_tickers(self.NSE_ALL_URL, series_filter='EQ')
        all_metrics = self.calculate_metrics(all_tickers, "ALL NSE")
        
        if not all_metrics.empty:
            # Identify Top 2% Leaders overall for Relative Strength
            all_metrics['momentum_rank'] = all_metrics['momentum_3m'].rank(pct=True)
            
            # Enrich liquid ones with fundamentals
            fundamental_eligible = self.enrich_fundamentals(all_metrics)

            with open(os.path.join(self.CONFIG_DIR, "comprehensive_universe.json"), "w") as f:
                json.dump({
                    "updated_at": datetime.now().isoformat(),
                    "symbols": fundamental_eligible['symbol'].tolist(),
                    "metadata": fundamental_eligible.to_dict(orient='records')
                }, f, indent=4)
            logger.info(f"Saved {len(fundamental_eligible)} NSE stocks for Fundamental analysis.")

if __name__ == "__main__":
    generator = UniverseGenerator()
    generator.run()
