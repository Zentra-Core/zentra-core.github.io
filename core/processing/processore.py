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
    "desktop": "file_manager",
    "download": "file_manager",
    "documents": "file_manager",
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
    logger.debug("PROCESSOR", f"Input received: '{user_text}' | Voice status: {voice_status}")
    
    # 1. Generate response from AI
    logger.debug("PROCESSOR", "Calling brain.generate_response()")
    raw_response = brain.generate_response(user_text, external_config=current_config)
    
    # 2. Plugin Tag and Tool Calls Analysis
    logger.debug("PROCESSOR", "Searching for tags or tool_calls in response...")
    
    # Removes <think>...</think> blocks produced by reasoning models (Qwen, DeepSeek-R1, etc.)
    # We do this here before any analysis to exclude internal reasoning from the output
    if isinstance(raw_response, str):
        raw_response = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL | re.IGNORECASE).strip()
        raw_response = re.sub(r'<think>.*$', '', raw_response, flags=re.DOTALL | re.IGNORECASE).strip()
    
    tags_found = []
    
    # Check if it's a structured response (Native Function Calling)
    is_tool_call_object = not isinstance(raw_response, str) and hasattr(raw_response, 'tool_calls') and raw_response.tool_calls
    
    if is_tool_call_object:
        logger.info("[PROCESSOR] Native Function Calling detected.")
        for call in raw_response.tool_calls:
            # call.function.name format: "tag__method"
            if "__" in call.function.name:
                tag, method = call.function.name.split("__", 1)
                try:
                    args = json.loads(call.function.arguments)
                except Exception as e:
                    logger.debug("PROCESSOR", f"Error parsing arguments: {e}")
                    args = {}
                
                # Tuple format: (module, args, "function_call", method)
                tags_found.append((tag.lower(), args, "function_call", method))
                logger.debug("PROCESSOR", f"Function call extracted: {tag.upper()}.{method}() with args {args}")
            else:
                logger.debug("PROCESSOR", f"Unknown function format: {call.function.name}")
        
        # Raw verbal text, if present, otherwise empty string to avoid exceptions
        original_response_text = getattr(raw_response, 'content', "") or ""
        raw_response = original_response_text
        logger.debug("PROCESSOR", f"Text associated with function call: '{raw_response}'")
    else:
        # If not a tool_call object, ensure it's a string
        if not isinstance(raw_response, str):
            raw_response = getattr(raw_response, 'content', "") or ""
            
        logger.debug("PROCESSOR", f"Raw response received: {len(raw_response)} characters")
        logger.debug("PROCESSOR", f"Content: '{raw_response[:200]}...'")
        
        # Search for standard tag [MODULE: command] (Legacy)
        matches_standard = re.findall(r'\[(\w+):(.*?)\]', raw_response)
        for tag, action in matches_standard:
            tags_found.append((tag.lower(), action.strip(), "standard", None))
            logger.debug("PROCESSOR", f"Standard tag found: {tag.upper()} -> '{action}'")
        
        # Search for simple tags [MODULE] (Legacy)
        matches_simple = re.findall(r'\[(\w+)\]', raw_response)
        for tag in matches_simple:
            if not any(t[0] == tag.lower() for t in tags_found):
                tags_found.append((tag.lower(), "", "simple", None))
                logger.debug("PROCESSOR", f"Simple tag found: {tag.upper()}")
                
    # Process ALL tests/tags found
    for original_tag, action_or_args, call_type, method_name in tags_found:
        # Determine the module to call (with mapping for legacy fallback)
        module_to_call = original_tag
        
        # If tag is "tag" (AI legacy error), try to map the action
        if original_tag == "tag" and not method_name and isinstance(action_or_args, str):
            clean_action = action_or_args.strip().lower()
            for keyword, module in TAG_MAPPING.items():
                if keyword in clean_action:
                    module_to_call = module
                    logger.debug("PROCESSOR", f"Mapped 'tag' with action '{clean_action}' to module {module}")
                    break
            else:
                logger.debug("PROCESSOR", f"Tag 'tag' with action '{action_or_args}' not mappable, ignored")
                continue
        
        if module_to_call in BLACKLIST:
            logger.debug("PROCESSOR", f"Module {module_to_call} blacklisted, ignored")
            continue
            
        logger.debug("PROCESSOR", f"Processing module {module_to_call.upper()} (original tag: {original_tag})")
        
        # Retrieve plugin (or legacy instance) directly from memory loader
        from core.system import plugin_loader
        plugin_obj = plugin_loader.get_plugin_module(module_to_call.upper(), legacy=False)
        is_legacy_oop = False
        if not plugin_obj:
            plugin_obj = plugin_loader.get_plugin_module(module_to_call.upper(), legacy=True)
            if plugin_obj:
                is_legacy_oop = True
        
        if plugin_obj:
            if is_legacy_oop and (hasattr(plugin_obj, "process_tag") or hasattr(plugin_obj, "elabora_tag")):
                # OOP Legacy execution
                method_to_call = "process_tag" if hasattr(plugin_obj, "process_tag") else "elabora_tag"
                logger.debug("PROCESSOR", f"Plugin {module_to_call} is OOP Legacy; calling {method_to_call}('{action_or_args}')")
                print(f"{YELLOW}[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}{RESET}")
                try:
                    # Execute with dynamically detected method name
                    exec_method = getattr(plugin_obj, method_to_call)
                    result = exec_method(action_or_args)
                    if result:
                        logger.info(f"[PROCESSOR] Plugin {module_to_call.upper()} output: {len(str(result))} chars")
                        print(f"{CYAN}[OUTPUT {module_to_call.upper()}]:\n{result}{RESET}")
                except Exception as e:
                    logger.error(f"[PROCESSOR] Legacy OOP execution error for {module_to_call}: {e}")
            
            elif method_name and hasattr(plugin_obj, "tools"):
                # Native execution (Class-based/Function Calling)
                logger.debug("PROCESSOR", f"Executing native function {method_name} in {module_to_call}")
                print(f"{YELLOW}[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}{RESET}")
                try:
                    method = getattr(plugin_obj.tools, method_name)
                    # Pass python arguments to method
                    result = method(**action_or_args) if action_or_args else method()
                    if result:
                        logger.info(f"[PROCESSOR] Tool {method_name} output: {len(str(result))} chars")
                        print(f"{CYAN}[OUTPUT {module_to_call.upper()}]:\n{result}{RESET}")
                except Exception as e:
                    logger.error(f"[PROCESSOR] Tool execution error for {method_name}: {e}")
                    
            elif hasattr(plugin_obj, "execute") and not method_name:
                # Old style execution (Legacy procedure: execute(command: str))
                logger.debug("PROCESSOR", f"Plugin {module_to_call} has 'execute'; calling with: '{action_or_args}'")
                print(f"{YELLOW}[SYSTEM] {translator.t('executing_module', module=module_to_call.upper())}{RESET}")
                try:
                    result = plugin_obj.execute(action_or_args)
                    if result:
                        logger.info(f"[PROCESSOR] Plugin {module_to_call.upper()} output: {len(str(result))} chars")
                        print(f"{CYAN}[OUTPUT {module_to_call.upper()}]: {result}{RESET}")
                except Exception as e:
                    logger.error(f"[PROCESSOR] Old Plugin execution error for {module_to_call}: {e}")
            else:
                logger.debug("PROCESSOR", f"Plugin {module_to_call} format error / missing expected methods.")
        else:
            logger.debug("PROCESSOR", f"Plugin {module_to_call} not loaded or inactive.")
    
    if not tags_found:
        logger.debug("PROCESSOR", "No tags/tools found in response")

    
        # 3. Video Output Cleaning
    logger.debug("PROCESSOR", "Removing tags for video output")
    video_response = re.sub(r'\[.*?:.*?\]', '', raw_response).strip()
    
    if not video_response:
        # Check if there were tags in the original response
        if re.search(r'\[.*?\]', raw_response):
            # Tags present, so a command was likely executed
            logger.debug("PROCESSOR", "Response contained only tags; command executed")
            video_response = translator.t('command_executed')
        else:
            # No tags and no response - model issue
            logger.warning("PROCESSOR", "Empty response received from model")
            video_response = translator.t('model_no_response_error')
    
    logger.debug("PROCESSOR", f"Final video response: {len(video_response)} characters")
    # Sanitizes for safe printing on Windows terminal
    video_response = filtri.clean_for_video(video_response)

    # 4. Voice Text Preparation
    clean_text = ""
    if voice_status:
        logger.debug("PROCESSOR", "Preparing text for speech synthesis")
        clean_text = filtri.clean_for_voice(video_response)
        logger.info("[PROCESSOR] Text filtered and prepared for speech synthesis.")
        logger.debug("PROCESSOR", f"Voice text: {len(clean_text)} characters")
        
    return video_response, clean_text