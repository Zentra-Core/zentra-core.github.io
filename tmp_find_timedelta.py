import sys
import os
from datetime import timedelta

# Add root to path
root = r"c:\Zentra-Core"
if root not in sys.path:
    sys.path.insert(0, root)

from zentra.app.config import ConfigManager

cfg = ConfigManager()

def find_timedelta(d, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            find_timedelta(v, f"{path}.{k}")
    elif isinstance(d, list):
        for i, v in enumerate(d):
            find_timedelta(v, f"{path}[{i}]")
    elif isinstance(d, timedelta):
        print(f"FOUND TIMEDELTA at {path}: {d}")

find_timedelta(cfg.config)
print("Scan complete.")
