#!/bin/bash

# Momentum Trader: Command Execution Script
# This script provides quick access to all trading system operations.
# Run this from the Momentum-Trader-Private directory.

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ensure we are in the script's directory
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:$(pwd)

echo -e "${BLUE}=== Momentum Trader Command Menu ===${NC}"
echo -e "${YELLOW}--- NEW MODEL-DRIVEN PATH ---${NC}"
echo "1) [Universe] Update High-Octane Dynamic Universe (NSE 500)"
echo "2) [Regime]   Train HMM Market Model (NIFTY 50)"
echo "3) [Plan]     Generate Morning Battle Plan"
echo "4) [Radar]    OPEN TRADING RADAR (Web Dashboard)"
echo "5) [EXECUTE]  Run Master Trading Session (OpenAlgo Bridge)"
echo ""
echo -e "${YELLOW}--- ANALYTICS & MAINTENANCE ---${NC}"
echo "6) [System]    Run System Integrity Check"
echo "7) [Data]      Update Cache (Convert CSV to Parquet)"
echo "8) [Analytics] View Quantitative Performance Metrics"
echo "9) [Analytics] Run Market Cycle Analysis"
echo ""
echo -e "${YELLOW}--- LEGACY / BACKTEST ---${NC}"
echo "10) [Backtest] Run Champion ORB Simulation"
echo "11) [Backtest] Run Qullamaggie Index Baseline"
echo "12) [System]   Run Manual Backup"
echo "q) Quit"
echo ""

read -p "Select an option: " choice

case $choice in
    1)
        echo -e "${GREEN}Fetching and Filtering NSE 500 for High ADR stocks...${NC}"
        python3 scripts/update_universe.py
        ;;
    2)
        echo -e "${GREEN}Training Hidden Markov Model for Regime Detection...${NC}"
        python3 scripts/train_regime_model.py
        ;;
    3)
        echo -e "${GREEN}Refreshing NSE snapshots and generating Morning Battle Plan...${NC}"
        python3 scripts/nse_data_ingest.py && python3 scripts/morning_battle_plan.py
        ;;
    4)
        echo -e "${GREEN}Opening Trading Radar in your browser...${NC}"
        # Use 'open' for macOS, 'xdg-open' for Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open extensions/momentum_trading/data/trading_radar.html
        else
            xdg-open extensions/momentum_trading/data/trading_radar.html
        fi
        ;;
    5)
        echo -e "${GREEN}Starting Master Trading Session (OpenAlgo Bridge)...${NC}"
        python3 extensions/momentum_trading/trading/master_orchestrator.py
        ;;
    6)
        echo -e "${GREEN}Running System Integrity Check...${NC}"
        python3 scripts/verify_system_integrity.py
        ;;
    7)
        echo -e "${GREEN}Updating Data Cache...${NC}"
        python3 scripts/convert_to_parquet.py
        ;;
    8)
        echo -e "${GREEN}Loading Performance Metrics...${NC}"
        python3 scripts/quantitative_metrics.py
        ;;
    9)
        echo -e "${GREEN}Running Cycle Analysis...${NC}"
        python3 scripts/cycle_analysis.py
        ;;
    10)
        echo -e "${GREEN}Starting ORB Simulation...${NC}"
        python3 scripts/orb_simulation.py
        ;;
    11)
        echo -e "${GREEN}Starting Baseline Simulation...${NC}"
        python3 scripts/baseline_simulation.py
        ;;
    12)
        echo -e "${GREEN}Performing Manual Backup...${NC}"
        bash scripts/backup_trading_data.sh
        ;;
    q)
        exit 0
        ;;
    *)
        echo "Invalid option."
        ;;
esac
