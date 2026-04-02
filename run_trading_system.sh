#!/bin/bash

# Momentum Trader: Command Execution Script
# This script provides quick access to all trading system operations.
# Run this from the Momentum-Trader-Private directory.

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Momentum Trader Command Menu ===${NC}"
echo "1) [Daily] Run System Integrity Check"
echo "2) [Daily] Generate Morning Battle Plan (JSON)"
echo "3) [Daily] Run Pre-Market Shortlist Check"
echo "4) [Weekly] Run Momentum Research (Updates Shortlist)"
echo "5) [Data] Sync NIFTY 200 Watchlist"
echo "6) [Data] Update Cache (Convert CSV to Parquet)"
echo "7) [Analytics] View Quantitative Performance Metrics"
echo "8) [Analytics] Run Market Cycle Analysis"
echo "9) [Backtest] Run Champion ORB Simulation"
echo "10) [Backtest] Run Qullamaggie Index Baseline"
echo "11) [System] Run Manual Backup"
echo "q) Quit"
echo ""

read -p "Select an option: " choice

case $choice in
    1)
        echo -e "${GREEN}Running System Integrity Check...${NC}"
        python3 scripts/verify_system_integrity.py
        ;;
    2)
        echo -e "${GREEN}Generating Morning Battle Plan...${NC}"
        python3 scripts/morning_battle_plan.py
        ;;
    3)
        echo -e "${GREEN}Running Pre-Market Check...${NC}"
        python3 scripts/scheduled_momentum.py
        ;;
    4)
        echo -e "${GREEN}Running Weekly Momentum Research...${NC}"
        python3 jarvis_trading.py ask "Run my weekly momentum research and add the top 5 to my shortlist" --agent momentum_trader
        ;;
    5)
        echo -e "${GREEN}Syncing NIFTY Watchlist...${NC}"
        python3 jarvis_trading.py ask "Sync my NIFTY watchlist" --agent momentum_trader
        ;;
    6)
        echo -e "${GREEN}Updating Data Cache...${NC}"
        python3 scripts/convert_to_parquet.py
        ;;
    7)
        echo -e "${GREEN}Loading Performance Metrics...${NC}"
        python3 scripts/quantitative_metrics.py
        ;;
    8)
        echo -e "${GREEN}Running Cycle Analysis...${NC}"
        python3 scripts/cycle_analysis.py
        ;;
    9)
        echo -e "${GREEN}Starting ORB Simulation...${NC}"
        python3 scripts/orb_simulation.py
        ;;
    10)
        echo -e "${GREEN}Starting Baseline Simulation...${NC}"
        python3 scripts/baseline_simulation.py
        ;;
    11)
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
