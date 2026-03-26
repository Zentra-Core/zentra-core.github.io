"""
MODULE: Simplified Resuscitation Monitor - Zentra Core
DESCRIPTION: Monitors config.json for restarts.
"""

import subprocess
import time
import os
import sys
import json

# Path configuration
MAIN_SCRIPT = "main.py"
CONFIG_FILE = "config.json"

def get_translator():
    language = "en"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                language = cfg.get("language", "en")
        except: pass
    
    translations = {
        "it": {
            "critical_missing": "[MONITOR] CRITICAL: {file} not found.",
            "starting": "[MONITOR] Starting Zentra...",
            "config_changed": "[MONITOR] config.json change detected. Terminating...",
            "reset_complete": "[MONITOR] Reset complete. Restarting in 2 seconds...",
            "error": "[MONITOR] Error: {error}"
        },
        "en": {
            "critical_missing": "[MONITOR] CRITICAL: {file} not found.",
            "starting": "[MONITOR] Starting Zentra...",
            "config_changed": "[MONITOR] config.json change detected. Terminating...",
            "reset_complete": "[MONITOR] Reset complete. Restarting in 2 seconds...",
            "error": "[MONITOR] Error: {error}"
        }
    }
    return lambda key, **kwargs: translations.get(language, translations["en"]).get(key, key).format(**kwargs)

t = get_translator()

def get_file_timestamp(path):
    if os.path.exists(path):
        return os.path.getmtime(path)
    return 0

def start_and_monitor():
    if not os.path.exists(MAIN_SCRIPT):
        print(t("critical_missing", file=MAIN_SCRIPT))
        return False

    last_config_time = get_file_timestamp(CONFIG_FILE)
    print(t("starting"))
    
    # Process startup
    process = subprocess.Popen([sys.executable, MAIN_SCRIPT])

    try:
        while process.poll() is None:
            time.sleep(1)
            
            # config.json check
            current_config_time = get_file_timestamp(CONFIG_FILE)
            if current_config_time > last_config_time + 1:
                # Check for flag set by app to avoid unnecessary restarts
                if os.path.exists(".config_saved_by_app"):
                    try: os.remove(".config_saved_by_app")
                    except: pass
                    last_config_time = current_config_time
                    continue
                    
                print(f"\n{t('config_changed')}")
                process.terminate()
                # Wait for process to close (max 5 seconds)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill() # Force close if unresponsive
                
                print(t("reset_complete"))
                time.sleep(2) # Safety pause for GPU
                return True
                
        # Natural exit:
        if process.returncode == 42:
            return True # Restart on F6 request
        else:
            return False # Normal closure or different error, do not restart
                    
    except Exception as e:
        print(t("error", error=e))
        process.kill()
    
    return False

if __name__ == "__main__":
    while True:
        success = start_and_monitor()
        if not success: break