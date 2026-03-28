#!/bin/bash

# Configuration
PROJECT_ROOT="/Users/svasudevan/Vibecode/PersonalAI/Momentum-Trader-Private"
BACKUP_BRANCH="backups"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "--- Starting Trading Data Backup: $TIMESTAMP ---"

cd "$PROJECT_ROOT" || exit

# 1. Ensure we are on a branch or have git initialized
if [ ! -d ".git" ]; then
    echo "Error: Git not initialized in $PROJECT_ROOT"
    exit 1
fi

# 2. Check if backup branch exists, create if not
if ! git rev-parse --verify "$BACKUP_BRANCH" >/dev/null 2>&1; then
    echo "Creating backup branch: $BACKUP_BRANCH"
    git checkout -b "$BACKUP_BRANCH"
else
    git checkout "$BACKUP_BRANCH"
fi

# 3. Add only relevant folders (configs and data)
# Note: We exclude large Parquet/CSV files if needed, but for now assuming we want the full history
git add extensions/momentum_trading/configs/
git add extensions/momentum_trading/data/*.csv
git add extensions/momentum_trading/data/*.json

# 4. Commit and Push
if git diff --cached --quiet; then
    echo "No changes to backup."
else
    git commit -m "Automated Backup: $TIMESTAMP"
    # Note: Replace 'origin' with your actual remote if different
    git push origin "$BACKUP_BRANCH"
    echo "Backup pushed to $BACKUP_BRANCH branch."
fi

# 5. Return to main/master (optional, but safer for the user)
# git checkout main

echo "--- Backup Complete ---"
