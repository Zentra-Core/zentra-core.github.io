"""
MODULE: zentra_bridge/webui/prompting.py
DESCRIPTION: Builds the full system prompt sent to the LLM on every request.
             Combines personality, memory context, capabilities and safety rules.
"""

import os
import logging

bridge_logger = logging.getLogger("WebUI_Bridge")


def build_system_prompt(config: dict, bridge_dir: str) -> str:
    """
    Composes and returns the complete system prompt.

    Args:
        config:     The full Zentra config dict (result of ConfigManager.config).
        bridge_dir: Absolute path to the Zentra-Core root directory.

    Returns:
        A single multi-line string ready to be inserted as the ``system`` role message.
    """
    try:
        from core.llm import brain
        from memory import brain_interface
        from core.i18n import translator
    except ImportError as exc:
        bridge_logger.error(f"[PROMPT] Failed to import core modules: {exc}")
        return "You are Zentra, an AI assistant."

    # --- Personality file ---
    personalita_file = config.get("ia", {}).get("personalita_attiva", "zentra.txt")
    path_p = os.path.join(bridge_dir, "personality", personalita_file)
    testo_personalita = ""
    if os.path.exists(path_p):
        try:
            with open(path_p, "r", encoding="utf-8") as fh:
                testo_personalita = fh.read()
        except Exception as exc:
            bridge_logger.warning(f"[PROMPT] Cannot read personality file: {exc}")

    # --- Long-term memory context ---
    try:
        memoria_identita = brain_interface.ottieni_contesto_memoria()
    except Exception as exc:
        bridge_logger.warning(f"[PROMPT] Memory context unavailable: {exc}")
        memoria_identita = ""

    # --- Plugin capabilities ---
    try:
        capacita = brain.carica_capacita()
    except Exception as exc:
        bridge_logger.warning(f"[PROMPT] Capabilities unavailable: {exc}")
        capacita = ""

    # --- Safety / identity rules ---
    try:
        regole = (
            f"{translator.t('identity_protocol')}\n"
            f"- {translator.t('rule_who_am_i')}\n"
            f"{translator.t('file_management_rules')}\n"
            f"- {translator.t('rule_list_files')}\n"
            f"- {translator.t('rule_read_file')}\n"
            f"\n{translator.t('root_security_instruction')}\n"
            f"{translator.t('root_security_desc')}\n"
        )
    except Exception as exc:
        bridge_logger.warning(f"[PROMPT] Translator unavailable: {exc}")
        regole = ""

    return (
        f"{testo_personalita}\n\n"
        f"{memoria_identita}\n\n"
        f"{capacita}\n\n"
        f"{regole}\n"
        "--- END OF SYSTEM INSTRUCTIONS ---"
    )
