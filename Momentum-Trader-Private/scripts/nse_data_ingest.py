#!/usr/bin/env python3
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class NSEDataIngestion:
    """Lightweight NSE ingestion pipeline inspired by NSE_Data_Downloader.

    Produces normalized local snapshots for downstream strategy scripts.
    """

    NIFTY500_URL = (
        "https://www.nseindia.com/api/equity-stockIndices"
        "?index=NIFTY%20500&selectValFormat=crores"
    )
    MARKET_INDICES_URL = "https://www.nseindia.com/api/allIndices"

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.output_dir = root / "extensions" / "momentum_trading" / "data" / "nse_ingestion"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )
        return s

    def _prime_session(self, s: requests.Session) -> None:
        # Prime cookies similarly to NSE_Data_Downloader session bootstrap.
        seed_urls = [
            "https://www.nseindia.com",
            "https://www.nseindia.com/market-data/live-equity-market",
            "https://www.nseindia.com/market-data/live-index-watch",
        ]
        for u in seed_urls:
            try:
                s.get(u, timeout=20)
            except Exception as exc:
                logger.debug("Session seed request failed for %s: %s", u, exc)

    def _download_json(self, s: requests.Session, url: str, referer: str) -> Dict:
        headers = {"Referer": referer}
        resp = s.get(url, headers=headers, timeout=60, allow_redirects=True)
        if resp.status_code in (401, 403):
            self._prime_session(s)
            resp = s.get(url, headers=headers, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _find_price_column(df: pd.DataFrame) -> str:
        candidates = [
            "Last Price",
            "LTP",
            "Close",
            "Closing Price",
            "Last",
            "lastPrice",
            "lastPrice",
            "last",
            "ltp",
            "Ltp",
        ]
        normalized = {c.strip().lower(): c for c in df.columns}
        for c in candidates:
            key = c.strip().lower()
            if key in normalized:
                return normalized[key]
        return ""

    def _build_symbol_prices(self, df: pd.DataFrame) -> Dict[str, float]:
        if df.empty:
            return {}

        sym_col = ""
        for c in ["Symbol", "SYMBOL", "symbol"]:
            if c in df.columns:
                sym_col = c
                break
        if not sym_col:
            return {}

        px_col = self._find_price_column(df)
        if not px_col:
            return {}

        out: Dict[str, float] = {}
        for _, row in df.iterrows():
            raw_sym = str(row.get(sym_col, "")).strip()
            if not raw_sym or raw_sym.lower() == "nan":
                continue
            symbol = raw_sym if raw_sym.endswith(".NS") else f"{raw_sym}.NS"
            try:
                out[symbol] = float(str(row.get(px_col, "")).replace(",", ""))
            except Exception:
                continue
        return out

    def run(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        s = self._session()
        self._prime_session(s)

        logger.info("Downloading NSE NIFTY 500 snapshot...")
        nifty500_json = self._download_json(
            s,
            self.NIFTY500_URL,
            "https://www.nseindia.com/market-data/live-equity-market",
        )

        logger.info("Downloading NSE market indices snapshot...")
        indices_json = self._download_json(
            s,
            self.MARKET_INDICES_URL,
            "https://www.nseindia.com/market-data/live-index-watch",
        )

        nifty500_rows = nifty500_json.get("data", []) if isinstance(nifty500_json, dict) else []
        indices_rows = indices_json.get("data", []) if isinstance(indices_json, dict) else []

        nifty500_df = pd.DataFrame(nifty500_rows)
        indices_df = pd.DataFrame(indices_rows)

        symbol_prices = self._build_symbol_prices(nifty500_df)

        index_values: Dict[str, float] = {}
        idx_name_col = ""
        for c in ["index", "Index Name", "Index", "indexSymbol", "symbol"]:
            if c in indices_df.columns:
                idx_name_col = c
                break
        idx_px_col = self._find_price_column(indices_df)
        if idx_name_col and idx_px_col:
            for _, row in indices_df.iterrows():
                idx_name = str(row.get(idx_name_col, "")).strip()
                if not idx_name or idx_name.lower() == "nan":
                    continue
                try:
                    index_values[idx_name] = float(
                        str(row.get(idx_px_col, "")).replace(",", "")
                    )
                except Exception:
                    continue

        now = datetime.now()
        stamp = now.strftime("%Y%m%d_%H%M%S")
        (self.output_dir / f"nifty500_{stamp}.json").write_text(
            json.dumps(nifty500_json, indent=2), encoding="utf-8"
        )
        (self.output_dir / f"market_indices_{stamp}.json").write_text(
            json.dumps(indices_json, indent=2), encoding="utf-8"
        )

        snapshot = {
            "generated_at": now.isoformat(),
            "symbol_prices": symbol_prices,
            "index_values": index_values,
            "counts": {
                "symbols": len(symbol_prices),
                "indices": len(index_values),
            },
        }

        latest_snapshot = self.output_dir / "latest_snapshot.json"
        latest_snapshot.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

        logger.info(
            "NSE ingestion complete. symbols=%s indices=%s file=%s",
            len(symbol_prices),
            len(index_values),
            latest_snapshot,
        )
        return symbol_prices, index_values


if __name__ == "__main__":
    NSEDataIngestion().run()
