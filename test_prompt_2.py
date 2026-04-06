import sys
import os
import json
from app.config import ConfigManager
import core.llm.brain as brain
from core.system import plugin_loader

cfg = ConfigManager()
plugin_loader.update_capability_registry(cfg.config)

class DummyClient:
    @staticmethod
    def generate(system_prompt, user_text, backend_config, llm_config, tools=None, images=None, extra_messages=None):
        with open("prompt_output.txt", "w", encoding="utf-8") as f:
            f.write(system_prompt)
        return "Test response"
        
brain.client = DummyClient

brain.generate_response("Test message", external_config=cfg.config)
