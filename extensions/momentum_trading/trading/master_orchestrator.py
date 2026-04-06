import logging
import json
from typing import List, Dict, Any
from extensions.momentum_trading.trading.floor import TradingFloor
from extensions.momentum_trading.trading.risk import RiskManager
from extensions.momentum_trading.trading.execution import OpenAlgoExecutor

logger = logging.getLogger(__name__)

class MasterTradingOrchestrator:
    """
    Final Layer: Orchestrates HMM Regime, Scanning, Risk, and OpenAlgo Execution.
    This connects the "Brain" (HMM) to the "Muscle" (OpenAlgo).
    """
    
    def __init__(self, dry_run: bool = True):
        self.floor = TradingFloor()
        self.risk_manager = RiskManager()
        self.executor = OpenAlgoExecutor()
        self.executor.is_dry_run = dry_run

    def run_morning_session(self):
        """
        Main execution flow:
        1. Get HMM Regime.
        2. Run Scanners guided by Regime.
        3. For each setup: Calculate Kelly Size & Risk.
        4. Place orders via OpenAlgo.
        """
        logger.info("--- Starting Master Trading Session ---")
        
        # 1. HMM Analysis
        report = self.floor.produce_unified_report()
        regime_data = report['market_regime']
        regime = regime_data['regime']
        recommendation = regime_data['recommendation']
        
        if regime == "BEARISH_VOLATILE":
            logger.warning("Market regime is BEARISH. Strategy is CASH. No trades will be placed.")
            return

        # 2. Iterate through prioritized strategy setups
        strategy_key = "momentum" if recommendation['primary'] == "MOMENTUM" else "reversion"
        setups = report['strategies'].get(strategy_key, [])
        
        if not setups:
            logger.info(f"No {strategy_key} setups found for today's regime ({regime}).")
            return

        logger.info(f"Processing {len(setups)} {strategy_key} setups...")

        for setup in setups:
            symbol = setup['symbol']
            # Note: In a real system, you'd fetch the current LTP here
            # For demonstration, we'll use price from setup if available
            entry_price = setup['data'].get('price', 0) 
            
            # Use ADR-based stop if available, otherwise fallback to 2%
            adr_value = setup['data'].get('scorecard', {}).get('adr_value', setup['data'].get('adr', 0))
            
            if adr_value > 0:
                stop_loss = self.risk_manager.calculate_adr_stop(entry_price, adr_value)
                sl_type = "ADR-based"
            else:
                stop_loss = entry_price * 0.98 
                sl_type = "Fallback 2%"
            
            if entry_price == 0:
                logger.warning(f"Skipping {symbol}: Entry price not found.")
                continue

            # 3. Calculate Risk & Position Size
            # Kelly sizing is adjusted by the HMM risk_multiplier (e.g. 0.8x or 1.2x)
            pos_details = self.risk_manager.get_position_details(symbol, strategy_key.upper(), entry_price, stop_loss)
            
            # Apply HMM Multiplier
            final_quantity = int(pos_details['quantity'] * recommendation['risk_multiplier'])
            
            # 4. Execute via OpenAlgo
            logger.info(f"PRE-TRADE: {symbol} | Regime: {regime} | SL: {stop_loss:.2f} ({sl_type}) | Kelly Qty: {pos_details['quantity']} | Adjusted Qty: {final_quantity}")
            
            self.executor.place_order(
                symbol=symbol,
                side="BUY",
                quantity=final_quantity,
                price=entry_price,
                stop_loss=stop_loss
            )

        logger.info("--- Master Trading Session Complete ---")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    master = MasterTradingOrchestrator(dry_run=True)
    master.run_morning_session()
