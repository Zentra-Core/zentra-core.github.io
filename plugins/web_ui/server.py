"""
WEB_UI Plugin — Server
Flask daemon thread that serves both the Config Panel and the native Chat UI.
"""
import threading
import logging
import os
from .routes import init_routes
from .routes_chat import init_chat_routes

log = logging.getLogger("ZentraWebUIServer")

_global_server_instance = None
_server_lock = threading.Lock()


class ZentraWebUIServer:
    def __init__(self, config_manager, root_dir: str, port: int, logger=None):
        self.config_manager = config_manager
        self.root_dir = root_dir
        self.port = port
        self.logger = logger or log
        self._thread = None

    def start(self) -> None:
        try:
            from flask import Flask
        except ImportError as e:
            self.logger.warning(f"[WebUI] Flask not available ({e})")
            return

        from core.i18n.translator import t

        # Templates are inside this plugin's own templates/ folder
        tpl_dir = os.path.join(os.path.dirname(__file__), "templates")
        app = Flask("ZentraWebUI", template_folder=tpl_dir)
        
        # Inject translation system into Jinja2 templates
        app.jinja_env.globals.update(t=t)

        # Silence werkzeug noise
        try:
            import logging as _lg
            _lg.getLogger("werkzeug").setLevel(_lg.ERROR)
            app.logger.disabled = True
        except Exception:
            pass

        # Register all routes
        init_routes(app, self.config_manager, self.root_dir, self.logger)
        init_chat_routes(app, self.config_manager, self.root_dir, self.logger)

        def _run():
            try:
                self.logger.info(
                    f"[WebUI] 🚀 Server live → "
                    f"http://127.0.0.1:{self.port}/chat  |  "
                    f"http://127.0.0.1:{self.port}/zentra/config/ui"
                )
                app.run(host="127.0.0.1", port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                self.logger.error(f"[WebUI] Flask exception: {e}")

        self._thread = threading.Thread(target=_run, daemon=True, name="ZentraWebUIThread")
        self._thread.start()


def start_if_needed(config_manager, root_dir: str, port: int = 7070) -> None:
    """Singleton entry point — safe to call multiple times."""
    global _global_server_instance
    with _server_lock:
        b_log = logging.getLogger("ZentraWebUI")
        try:
            alive = (_global_server_instance is not None
                     and _global_server_instance._thread is not None
                     and _global_server_instance._thread.is_alive())
            if not alive:
                b_log.info(f"[WebUI] Starting server on port {port}.")
                srv = ZentraWebUIServer(config_manager, root_dir, port, logger=b_log)
                srv.start()
                _global_server_instance = srv
        except Exception as e:
            b_log.error(f"[WebUI] Startup error: {e}")


# ── Standalone (.bat launcher) ────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    os.chdir(root)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    from app.config import ConfigManager
    from core.i18n.translator import init_translator
    cfg = ConfigManager()
    
    # Initialize translator with current config language
    init_translator(cfg.get("language", "en"))

    start_if_needed(cfg, root, port=7070)

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Zentra WebUI server stopped.")
