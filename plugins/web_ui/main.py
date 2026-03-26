"""
Plugin: WEB_UI
Serves the Zentra native chat interface and config panel on localhost:7070.
"""
import os
import sys
import logging
import threading
import webbrowser

try:
    from core.logging import logger
    from core.i18n import translator
    from app.config import ConfigManager
    _HAVE_CORE = True
except ImportError:
    _HAVE_CORE = False
    class _L:
        def info(self, *a, **k): print("[WEB_UI]", *a)
        def warning(self, *a, **k): print("[WEB_UI WARN]", *a)
        def debug(self, *a, **k): pass
        def error(self, *a, **k): print("[WEB_UI ERR]", *a)
    logger = _L()
    class _T:
        def t(self, k, **kw): return k
    translator = _T()

# Ensure the project root is importable
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

class WebUIPlugin:
    """
    Zentra Native Web UI Plugin.
    Starts the embedded Flask server that serves:
      - http://127.0.0.1:7070/chat         → Chat interface
      - http://127.0.0.1:7070/zentra/config/ui → Config Panel
    """

    def __init__(self):
        self.tag   = "WEB_UI"
        self.desc  = "Native Web Interface — Chat + Config Panel on localhost:7070"
        
        self.config_schema = {
            "port": {
                "type": "int",
                "default": 7070,
                "min": 1024,
                "max": 65535,
                "description": "HTTP port for the Web UI server"
            },
            "auto_open_browser": {
                "type": "bool",
                "default": False,
                "description": "Open the browser automatically on startup"
            }
        }

        cfg_mgr = ConfigManager() if _HAVE_CORE else None
        port = 7070
        if cfg_mgr:
            port = cfg_mgr.config.get("plugins", {}).get("WEB_UI", {}).get("port", 7070)
            auto_open = cfg_mgr.config.get("plugins", {}).get("WEB_UI", {}).get("auto_open_browser", False)
        else:
            auto_open = False

        self._port = port
        self._url  = f"http://127.0.0.1:{port}"

        # Launch the HTTP server (singleton — safe to call multiple times)
        try:
            from plugins.web_ui.server import start_if_needed
            start_if_needed(cfg_mgr, _ROOT, port=port)
            logger.info(f"[WEB_UI] Server started → {self._url}/chat")
        except Exception as e:
            logger.warning(f"[WEB_UI] Server startup error: {e}")

        if auto_open:
            threading.Timer(1.5, lambda: webbrowser.open(f"{self._url}/chat")).start()

    @property
    def status(self) -> str:
        return f"Online → {self._url}/chat"

    def get_panel_url(self) -> str:
        """Returns the URL of the chat interface."""
        return f"{self._url}/chat"

    def open_browser(self) -> str:
        """Opens the Zentra web interface in the default browser."""
        try:
            webbrowser.open(f"{self._url}/chat")
            return f"Browser opened at {self._url}/chat"
        except Exception as e:
            return f"Could not open browser: {e}"


# ── Public plugin instance ────────────────────────────────────────────────────
tools = WebUIPlugin()


def esegui(comando: str) -> str:
    cmd = comando.lower().strip()
    if cmd in ("open", "apri", "browser"):
        return tools.open_browser()
    return tools.get_panel_url()


def info() -> dict:
    return {
        "tag":      "WEB_UI",
        "desc":     tools.desc,
        "comandi": {
            "open":   "Open web interface in default browser",
            "status": "Show interface URL"
        }
    }
