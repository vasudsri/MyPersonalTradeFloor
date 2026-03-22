#!/bin/bash
# Setup Script for Momentum Trader Extension
# This script links your private trading logic into a local OpenJarvis instance.

if [ -z "$1" ]; then
    echo "Usage: ./setup_extension.sh /path/to/OpenJarvis"
    exit 1
fi

# Get absolute path of JARVIS_DIR
JARVIS_DIR=$(cd "$1" && pwd)
# Get absolute path of where this script is located
PRIVATE_REPO_DIR=$(cd "$(dirname "$0")" && pwd)

echo "Setting up Momentum Trader Extension in $JARVIS_DIR..."

# 1. Create extensions link
mkdir -p "$JARVIS_DIR/extensions"
ln -sfn "$PRIVATE_REPO_DIR/extensions/momentum_trading" "$JARVIS_DIR/extensions/momentum_trading"

# 2. Link the entry point shim
ln -sfn "$PRIVATE_REPO_DIR/jarvis_trading.py" "$JARVIS_DIR/jarvis_trading.py"

# 3. Ensure dependencies are present
cd "$JARVIS_DIR"
uv add yfinance pandas requests

echo "------------------------------------------------"
echo "Setup Complete!"
echo "You can now run scans using:"
echo "uv run python jarvis_trading.py ask \"Run weekly research\" --agent momentum_trader"
echo "------------------------------------------------"
