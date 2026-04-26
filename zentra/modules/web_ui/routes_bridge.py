import os
import sys
import json
import threading
from flask import request, jsonify

# File-based queue for cross-process communication (avoids multi-worker isolation)
_QUEUE_LOCK = threading.Lock()

def _get_queue_path():
    """Returns the path to the bridge command queue file."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(root, ".bridge_queue.json")

def _read_queue():
    path = _get_queue_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _write_queue(cmds: list):
    path = _get_queue_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cmds, f)
    except Exception:
        pass

def init_bridge_routes(app, logger):
    """
    Initializes the bridge endpoints for Session 0 -> Session 1 communication.
    Uses a file-based queue to persist commands across Flask worker processes.
    """

    @app.route("/api/bridge/command", methods=["POST"])
    def bridge_command():
        """WebUI (or Core) calls this to request a GUI action from the Tray App."""
        try:
            data = request.get_json(force=True) or {}
            cmd  = data.get("cmd")
            path = data.get("path")
            
            if not cmd:
                return jsonify({"ok": False, "error": "Missing command"}), 400
                
            command_item = {
                "id": os.urandom(4).hex(),
                "cmd": cmd,
                "path": path,
            }
            
            with _QUEUE_LOCK:
                cmds = _read_queue()
                cmds.append(command_item)
                # Cap queue size
                if len(cmds) > 20:
                    cmds = cmds[-20:]
                _write_queue(cmds)
                
            logger.info(f"[BRIDGE] Queued command: {cmd} for {path}")
            return jsonify({"ok": True, "msg": "Command queued"})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.route("/api/bridge/poll", methods=["GET"])
    def bridge_poll():
        """Tray App (Session 1) calls this to check for pending actions."""
        try:
            with _QUEUE_LOCK:
                cmds = _read_queue()
                if not cmds:
                    return jsonify({"ok": True, "commands": []})
                
                # Clear the queue and return commands
                _write_queue([])
                
            logger.info(f"[BRIDGE] Commands dispatched to Tray: {[c['cmd'] for c in cmds]}")
            return jsonify({"ok": True, "commands": cmds})
        except Exception as e:
            logger.error(f"[BRIDGE] Poll error: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
