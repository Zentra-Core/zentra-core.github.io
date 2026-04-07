import os
import json
from zentra.core.logging import logger

class AutoCoderTools:
    def __init__(self):
        self.desc = "Zentra AutoCoder Tools. Usa questi tool per analizzare o scrivere codice nel sistema in maniera autonoma."
        self.tag = "AUTOCODER"
        self.status = "ONLINE"
        # Optional config schema used by WebUI Editor
        self.config_schema = {
            "sandbox_only": {"type": "bool", "default": False, "desc": "Restrict modifications to experimental folder"}
        }

    def read_file(self, file_path: str, start_line: int = 1, end_line: int = -1) -> str:
        """Reads the exact contents of a file. Pass start_line and end_line bounds to limit output verbosity."""
        try:
            if not os.path.exists(file_path):
                return f"[AUTOCODER ERROR] File non trovato: {file_path}"
                
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            if end_line == -1:
                end_line = len(lines)
                
            start_index = max(0, start_line - 1)
            output = "".join(lines[start_index:end_line])
            return f"--- Contenuto {file_path} (Linee {start_line}-{end_line}) ---\n{output}"
        except Exception as e:
            return f"[AUTOCODER ERROR] Lettura fallita: {str(e)}"

    def write_file(self, file_path: str, content: str, mode: str = "w") -> str:
        """Writes or creates a new file. Mode 'w' overwrites."""
        try:
            from zentra.app.config import ConfigManager
            cfg = ConfigManager().config
            sandbox_only = cfg.get("plugins", {}).get(self.tag, {}).get("sandbox_only", False)
            
            # Simple sandbox lock
            if sandbox_only and "experimental" not in file_path.lower():
                return f"[AUTOCODER ERROR] Sandbox abilitato. Non hai il permesso di scrivere fuori dalla cartella 'experimental'."
                
            # Auto-create directories
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, mode, encoding="utf-8") as f:
                f.write(content)
                
            return f"[AUTOCODER OK] File {file_path} scritto con successo."
        except Exception as e:
            return f"[AUTOCODER ERROR] Scrittura fallita: {str(e)}"

    def list_dir(self, directory_path: str) -> str:
        """Lists directory contents."""
        try:
            if not os.path.exists(directory_path):
                return f"[AUTOCODER ERROR] Directory non trovata: {directory_path}"
                
            items = os.listdir(directory_path)
            output = f"--- Contenuto di {directory_path} ---\n"
            for item in items:
                output += f"- {item}\n"
            return output
        except Exception as e:
            return f"[AUTOCODER ERROR] Listing fallito: {str(e)}"

# Entrypoint per lo scanner di Plugin
tools = AutoCoderTools()
