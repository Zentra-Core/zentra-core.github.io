import sys
import os
import json
from app.config import ConfigManager
import core.llm.brain as brain
from core.system import plugin_loader

cfg = ConfigManager()
plugin_loader.update_capability_registry(cfg.config)

print(f"Active personality: {cfg.config.get('ai', {}).get('active_personality')}")

class DummyClient:
    @staticmethod
    def generate(system_prompt, user_text, backend_config, llm_config, tools=None, images=None, extra_messages=None):
        print("=== SYSTEM PROMPT ===")
        print(system_prompt)
        print("=====================")
        return "Test response"
        
brain.client = DummyClient

print("Calling generate_response...")
brain.generate_response("Test message", external_config=cfg.config)
