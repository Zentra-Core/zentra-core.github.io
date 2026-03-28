"""
MODULE: Logical Processor - Zentra Core v2.5
DESCRIPTION: The 'execution engine'. Transforms AI thought into real actions 
via plugins and filters text for speech synthesis.
"""
import sys
import re
import os
import json

import importlib.util
from core.llm import brain
from core.processing import filtri
from core.logging import logger
from core.i18n import translator

# Colors for terminal logs
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
RESET = '\033[0m'

# Global variable to hold hardware parameters
current_config = {}

# Blacklist of tags to ignore
BLACKLIST = ["titolo", "anima", "regole", "database", "status", "tag"]

# Mapping for generic tags to the correct module
TAG_MAPPING = {
    "terminal": "system",
    "cmd": "system",
    "instruction": "system",
    "open": "system",
    "notepad": "system",
    "chrome": "system",
    "visual studio": "system",
    "sillytavern": "system",
    "desktop": "system",
    "download": "system",
    "documents": "system",
    "core": "file_manager",

    "plugins": "file_manager",
    "memory": "file_manager",
    "personality": "file_manager",
    "logs": "file_manager",
    "config": "file_manager",
    "main": "file_manager",
    # Legacy fallbacks
    "terminale": "system",
    "istruzione": "system",
    "apri": "system",
    "documenti": "file_manager",
}

def configure(new_config):
    """Receives configuration from Main and stores it for Brain calls."""
    global current_config
    current_config = new_config
    logger.info("[PROCESSOR] Hardware configuration synchronized.")


def process_exchange(user_text, voice_status):
    """Manages the entire chain: AI -> Plugin -> Cleaning -> Response."""
    logger.info(f"[PROCESSOR] Input received: '{user_text}'. Calling brain...")
    
    # 1. Generate response from AI
    raw_response = brain.generate_response(user_text, external_config=current_config)
    
    # 2. Process tags and clean response
    return process(raw_response, config=current_config, voice_status=voice_status)


def process(raw_response, config=None, voice_status=False):
    """
    Processes a raw LLM response: executes tags/tools and cleans the text for video/voice.
    """
    global current_config
    if config:
        current_config = config

    # 1. Ignore error messages from the Brain
    if isinstance(raw_response, str) and raw_response.startswith("ZENTRA:"):
        logger.debug("PROCESSOR", "Ignoring internal ZENTRA error message for tag processing")
        return raw_response, ""

    # 1. Reasoning removal (<think> tags)
    if isinstance(raw_response, str):
        raw_response = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL | re.IGNORECASE).strip()
        raw_response = re.sub(r'<think>.*$', '', raw_response, flags=re.DOTALL | re.IGNORECASE).strip()
    
    tags_found = []
    
    # 2. Structured response (Native Function Calling)
    is_tool_call_object = not isinstance(raw_response, str) and hasattr(raw_response, 'tool_calls') and raw_response.tool_calls
    
    if is_tool_call_object:
        logger.info("[PROCESSOR] Native Function Calling detected.")
        for call in raw_response.tool_calls:
            if "__" in call.function.name:
                tag, method = call.function.name.split("__", 1)
                try:
                    args = json.loads(call.function.arguments)
                    logger.debug("PROCESSOR", f"Tool call: {tag}.{method}({args})")
                except Exception as e:
                    logger.error("PROCESSOR", f"Error parsing arguments: {e}")
                    args = {}
                tags_found.append((tag.lower(), args, "function_call", method))
            else:
                logger.debug("PROCESSOR", f"Unknown function format: {call.function.name}")
        
        original_response_text = getattr(raw_response, 'content', "") or ""
        raw_response = original_response_text
    else:
        if not isinstance(raw_response, str):
            raw_response = getattr(raw_response, 'content', "") or ""
            
        logger.debug("PROCESSOR", f"Processing text for tags: '{raw_response[:200]}...'")
        
        # Legacy Tag parsing
        matches_standard = re.findall(r'\[(\w+):(.*?)\]', raw_response)
        for tag, action in matches_standard:
            logger.info(f"[PROCESSOR] Standard tag: [{tag}:{action}]")
            tags_found.append((tag.lower(), action.strip(), "standard", None))
        
        matches_simple = re.findall(r'\[(\w+)\]', raw_response)
        for tag in matches_simple:
            if not any(t[0] == tag.lower() for t in tags_found):
                logger.info(f"[PROCESSOR] Simple tag: [{tag}]")
                tags_found.append((tag.lower(), "", "simple", None))
                
    # 3. Execution
    tool_results = []
    for original_tag, action_or_args, call_type, method_name in tags_found:
        module_to_call = original_tag
        
        if original_tag == "tag" and not method_name and isinstance(action_or_args, str):
            clean_action = action_or_args.strip().lower()
            for keyword, module in TAG_MAPPING.items():
                if keyword in clean_action:
                    module_to_call = module
                    break
            else: continue
        
        if module_to_call in BLACKLIST: continue
            
        from core.system import plugin_loader
        plugin_obj = plugin_loader.get_plugin_module(module_to_call.upper(), legacy=False)
        is_legacy_oop = False
        if not plugin_obj:
            plugin_obj = plugin_loader.get_plugin_module(module_to_call.upper(), legacy=True)
            if plugin_obj: 
                is_legacy_oop = True
                logger.debug("PROCESSOR", f"Found legacy OOP plugin for {module_to_call}")
        else:
            logger.debug("PROCESSOR", f"Found native plugin for {module_to_call}")
        
        if plugin_obj:
            logger.debug("PROCESSOR", f"Analyzing plugin {module_to_call}: legacy_oop={is_legacy_oop}, has_tools={hasattr(plugin_obj, 'tools')}, has_execute={hasattr(plugin_obj, 'execute')}")
            
            if is_legacy_oop and (hasattr(plugin_obj, "process_tag") or hasattr(plugin_obj, "elabora_tag")):
                method_to_call = "process_tag" if hasattr(plugin_obj, "process_tag") else "elabora_tag"
                logger.info(f"[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}")
                try:
                    exec_method = getattr(plugin_obj, method_to_call)
                    result = exec_method(action_or_args)
                    if result:
                        logger.info(f"[OUTPUT {module_to_call.upper()}]:\n{result}")
                        tool_results.append(str(result))
                except Exception as e:
                    logger.error(f"[PROCESSOR] Legacy OOP error: {e}")
            
            elif method_name and hasattr(plugin_obj, "tools"):
                logger.info(f"[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}")
                try:
                    method = getattr(plugin_obj.tools, method_name)
                    result = method(**action_or_args) if action_or_args else method()
                    if result:
                        logger.info(f"[OUTPUT {module_to_call.upper()}]:\n{result}")
                        tool_results.append(str(result))
                except Exception as e:
                    logger.error(f"[PROCESSOR] Tool error: {e}")
                    
            elif hasattr(plugin_obj, "execute") and not method_name:
                logger.info(f"[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}")
                try:
                    result = plugin_obj.execute(action_or_args)
                    if result:
                        logger.info(f"[OUTPUT {module_to_call.upper()}]: {result}")
                        tool_results.append(str(result))
                except Exception as e:
                    logger.error(f"[PROCESSOR] Old Plugin error: {e}")
    
    # 4. Cleaning
    base_video = re.sub(r'\[.*?:.*?\]', '', raw_response).strip()
    base_video = re.sub(r'\[.*?\]', '', base_video).strip() # Remove simple tags too
    
    if not base_video:
        if tags_found:
            base_video = translator.t('command_executed')
        else:
            base_video = translator.t('model_no_response_error')
    
    video_response = filtri.clean_for_video(base_video)
    
    clean_voice_text = ""
    if voice_status:
        # We use base_video so Zentra speaks only her intention, not the raw JSON/logs.
        clean_voice_text = filtri.clean_for_voice(base_video)
        
    if tool_results:
        # Append raw plugin results explicitly to the GUI chat window (video_response)
        video_response += "\n\n" + "\n\n".join(tool_results)
        
    return video_response, clean_voice_text
