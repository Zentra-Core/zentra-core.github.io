import sys
import os

from app.config import ConfigManager
c = ConfigManager()
print("BEFORE:")
print(c.get("backend", "cloud", "model"))
ok = c.update_config({"backend": {"cloud": {"model": "gemini/gemini-2.5-flash"}}})
print("UPDATE SUCCESS:", ok)
print("AFTER:")
print(c.get("backend", "cloud", "model"))
