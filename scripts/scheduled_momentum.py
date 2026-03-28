#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from openjarvis import Jarvis
# Import tools to register them
import extensions.momentum_trading.tools.qullamaggie 

def main():
    # Use a capable model for strategy analysis
    model = "qwen2.5:7b" 
    
    print(f"--- Momentum Trader Pre-Market Check ---")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("---------------------------------------")
    
    j = Jarvis(model=model)

    query = "Perform the 08:45 IST Pre-Market check. Run the daily entry tracker on the current shortlist and summarize any setups."

    try:
        response = j.ask(
            query,
            agent="momentum_trader"
        )
        
        print("\n=== PRE-MARKET ANALYSIS ===")
        print(response)
        
        # Save report to a local file for history
        log_dir = "Momentum-Trader-Private/extensions/momentum_trading/reports"
        os.makedirs(log_dir, exist_ok=True)
        filename = f"{log_dir}/pre_market_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, "w") as f:
            f.write(response)
        print(f"\nReport saved to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        j.close()

if __name__ == "__main__":
    main()
