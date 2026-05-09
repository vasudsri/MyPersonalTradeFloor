#!/usr/bin/env python3
"""
Momentum Trader Entry Point
This script ensures the 'extensions/' directory is correctly loaded
before calling the standard OpenJarvis logic.
"""
import os
import sys
import importlib

# 1. Add current directory to path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# 2. Force load extensions
def load_extensions():
    ext_path = os.path.join(root_dir, "extensions")
    if os.path.exists(ext_path):
        for item in os.listdir(ext_path):
            item_path = os.path.join(ext_path, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__init__.py")):
                try:
                    # Import the package and its sub-packages
                    pkg = importlib.import_module(f"extensions.{item}")
                    for sub in ["agents", "tools"]:
                        sub_path = os.path.join(item_path, sub)
                        if os.path.exists(os.path.join(sub_path, "__init__.py")):
                            importlib.import_module(f"extensions.{item}.{sub}")
                except Exception as e:
                    print(f"Warning: Failed to load extension {item}: {e}")

load_extensions()

# 3. Hand over to the standard CLI
from openjarvis.cli import main
if __name__ == "__main__":
    main()
