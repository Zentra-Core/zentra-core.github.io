import sys
from app.config import ConfigManager
from config.schemas.system_schema import SystemConfig
import json

c = ConfigManager()
print(f"Current model in dict: {c.config.get('backend', {}).get('cloud', {}).get('model')}")
print(f"Current model in Pydantic: {c._model.backend.cloud.model}")

print("\n--- Testing update_config ---")
update_payload = {"backend": {"cloud": {"model": "gemini/gemini-2.5-flash"}}}
print(f"Payload: {update_payload}")

# Manually simulate update_config to see error
c.reload()
c._deep_update(c.config, update_payload)
try:
    c._model = SystemConfig.model_validate(c.config)
    print("VALIDATION SUCCESS")
except Exception as e:
    print(f"VALIDATION FAILED: {e}")

print(f"Resulting model in Pydantic: {c._model.backend.cloud.model}")
