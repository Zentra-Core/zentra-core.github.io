import sys
import os
import importlib.util

main_file = "plugins/sys_net/main.py"
spec = importlib.util.spec_from_file_location("plugins.sys_net.main", main_file)
try:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("LOADED SUCCESSFULLY")
    print(getattr(module, "tools").tag)
except Exception as e:
    print(f"ERROR: {e}")
