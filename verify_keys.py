import os
import sys
import yaml
from dotenv import load_dotenv

# Replicating Zentra's loading logic
load_dotenv()

config_path = r"c:\Zentra-Core\config\system.yaml"
with open(config_path, "r") as f:
    cfg = yaml.safe_load(f)

gemini_cfg_key = cfg.get("llm", {}).get("providers", {}).get("gemini", {}).get("api_key", "").strip()
env_key = os.environ.get("GEMINI_API_KEY", "").strip()

print(f"--- DIAGNOSTICA API KEY ---")
print(f"YAML Key (first 4 chars): {gemini_cfg_key[:4]}... (Length: {len(gemini_cfg_key)})")
print(f"ENV Key (first 4 chars):  {env_key[:4]}... (Length: {len(env_key)})")

if gemini_cfg_key:
    print(f"RISULTATO: Verrà usata la chiave dello YAML.")
else:
    print(f"RISULTATO: Verrà usata la chiave dell'ambiente (.env).")
