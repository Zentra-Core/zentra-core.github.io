import os
import json
from flask import request, jsonify, render_template

def init_routes(app, cfg_mgr, root_dir, logger, get_sm=None):
    """
    get_sm: callable that returns the current StateManager (or None).
    Using a getter ensures late-binding after the server starts.
    """
    def _sm():
        return get_sm() if callable(get_sm) else get_sm


    @app.route("/zentra/config/ui")
    def config_ui():
        try:
            return render_template("index.html")
        except Exception as e:
            return f"<h1>Errore: index.html non trovato</h1><p>{str(e)}</p>", 500

    @app.route("/zentra/config", methods=["GET"])
    def get_config():
        cfg = cfg_mgr.reload()
        return jsonify(cfg)

    @app.route("/api/models/refresh", methods=["POST"])
    def refresh_models():
        from app.model_manager import ModelManager
        mm = ModelManager(cfg_mgr)
        mm.get_available_models() # This updates the cache in config
        return jsonify({"ok": True})

    @app.route("/zentra/options", methods=["GET"])
    def get_options():
        import glob
        cfg = cfg_mgr.reload()
        
        piper_path_dir = r"C:\piper"
        try:
            onnx_files = [os.path.basename(f) for f in glob.glob(os.path.join(piper_path_dir, "*.onnx"))]
            if not onnx_files: onnx_files = ["en_US-lessac-medium.onnx"]
        except:
            onnx_files = ["en_US-lessac-medium.onnx"]
            
        from app.model_manager import ModelManager
        mm = ModelManager(cfg_mgr)
        categorized = mm.get_available_models()
        
        ollama_models = categorized.get("Ollama (Local)", [])
        personalita   = list(cfg.get("ai", {}).get("available_personalities", {}).values())
        
        # Flatten cloud models for the simple dropdown
        cloud_models_flat = []
        cloud_by_provider = {}
        for cat, models in categorized.items():
            if "Cloud" in cat:
                cloud_models_flat.extend(models)
                provider = cat.replace("Cloud (", "").replace(")", "").lower()
                cloud_by_provider[provider] = models

        return jsonify({
            "piper_voices": onnx_files,
            "piper_dir":    piper_path_dir,
            "ollama_models": ollama_models,
            "personalities": personalita,
            "cloud_models":  cloud_by_provider,
            "all_cloud":     cloud_models_flat
        })

    @app.route("/zentra/config", methods=["POST"])
    def post_config():
        try:
            incoming = request.get_json(force=True)
            if not isinstance(incoming, dict):
                return jsonify({"ok": False, "error": "Invalid payload"}), 400
            cfg_mgr.config = incoming
            if cfg_mgr.save():
                # Dynamically update the global translator language without reboot
                from core.i18n.translator import get_translator
                get_translator().set_language(incoming.get("language", "en"))
                # Keep state_manager in sync with saved audio_mode
                sm = _sm()
                if sm is not None:
                    sm.audio_mode = incoming.get("audio_mode", "auto")
                    sm.voice_status = incoming.get("voice", {}).get("voice_status", sm.voice_status)
                    sm.listening_status = incoming.get("listening", {}).get("listening_status", sm.listening_status)
                return jsonify({"ok": True})
            return jsonify({"ok": False, "error": "Save failed"}), 500
        except Exception as exc:
            logger.error(f"[WebUI] POST /config error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/zentra/status", methods=["GET"])
    def get_status():
        try:
            cfg     = cfg_mgr.config
            backend = cfg.get("backend", {}).get("type", "?")
            if   backend == "cloud":  model = cfg.get("backend", {}).get("cloud",  {}).get("model", "?")
            elif backend == "ollama": model = cfg.get("backend", {}).get("ollama", {}).get("model", "?")
            elif backend == "kobold": model = cfg.get("backend", {}).get("kobold", {}).get("model", "?")
            else: model = "?"

            br      = cfg.get("bridge", {})
            voice   = cfg.get("voice", {})
            listen  = cfg.get("listening", {})

            flags = [k for k, v in [
                ("proc",        br.get("use_processor")),
                ("think-strip", br.get("remove_think_tags")),
                ("tools",       br.get("enable_tools")),
            ] if v]

            # Read live state from state_manager if available, else fall back to config
            sm = _sm()
            if sm is not None:
                mic_on     = sm.listening_status
                tts_on     = sm.voice_status
                audio_mode = sm.audio_mode
            else:
                mic_on     = listen.get("listening_status", False)
                tts_on     = voice.get("voice_status", False)
                audio_mode = cfg.get("audio_mode", "auto")

            mic_status = "ON" if mic_on else "OFF"
            tts_status = "ON" if tts_on else "OFF"
            ptt_on     = listen.get("push_to_talk", False)
            ptt_status = "ON" if ptt_on else "OFF"

            from datetime import datetime
            config_path = os.path.join(root_dir, "config.json")
            mtime = os.path.getmtime(config_path) if os.path.exists(config_path) else 0
            ts    = datetime.fromtimestamp(mtime).strftime("%H:%M:%S") if mtime else "?"

            return jsonify({
                "backend":    backend.upper(),
                "model":      model,
                "bridge":     ", ".join(flags) if flags else "default",
                "mic":        mic_status,
                "tts":        tts_status,
                "ptt":        ptt_status,
                "audio_mode": audio_mode,
                "config":     f"last save {ts}",
            })
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    # ── Audio Control API ─────────────────────────────────────────────────────

    @app.route("/api/audio/toggle/mic", methods=["POST"])
    def toggle_mic():
        """Toggle listening_status — mirrors F4 on the console."""
        try:
            sm = _sm()
            if sm is None:
                return jsonify({"ok": False, "error": "State manager not available"}), 503
            new_val = not sm.listening_status
            sm.listening_status = new_val
            cfg_mgr.set(new_val, "listening", "listening_status")
            if cfg_mgr.save():
                logger.info(f"[WebUI] MIC toggled to {new_val} and saved.")
            else:
                logger.error("[WebUI] Failed to save MIC toggle.")
            # Keep processore in sync
            try:
                from core.processing import processore
                processore.configure(cfg_mgr.config)
            except Exception:
                pass
            return jsonify({"ok": True, "listening_status": new_val})
        except Exception as exc:
            logger.error(f"[WebUI] toggle_mic error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/toggle/tts", methods=["POST"])
    def toggle_tts():
        """Toggle voice_status — mirrors F5 on the console."""
        try:
            sm = _sm()
            if sm is None:
                return jsonify({"ok": False, "error": "State manager not available"}), 503
            new_val = not sm.voice_status
            sm.voice_status = new_val
            cfg_mgr.set(new_val, "voice", "voice_status")
            if cfg_mgr.save():
                logger.info(f"[WebUI] TTS toggled to {new_val} and saved.")
            else:
                logger.error("[WebUI] Failed to save TTS toggle.")
            try:
                from core.processing import processore
                processore.configure(cfg_mgr.config)
            except Exception:
                pass
            return jsonify({"ok": True, "voice_status": new_val})
        except Exception as exc:
            logger.error(f"[WebUI] toggle_tts error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/toggle/ptt", methods=["POST"])
    def toggle_ptt():
        """Toggle push_to_talk flag — mirrors F8 on the console."""
        try:
            sm = _sm()
            current_val = cfg_mgr.get("listening", "push_to_talk", default=False)
            new_val = not current_val
            cfg_mgr.set(new_val, "listening", "push_to_talk")
            if cfg_mgr.save():
                logger.info(f"[WebUI] PTT toggled to {new_val} and saved.")
            else:
                logger.error("[WebUI] Failed to save PTT toggle.")
            # Synchronize the live StateManager
            if sm is not None:
                sm.push_to_talk = new_val
            return jsonify({"ok": True, "push_to_talk": new_val})
        except Exception as exc:
            logger.error(f"[WebUI] toggle_ptt error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/mode", methods=["POST"])
    def set_audio_mode():
        """Set audio_mode: console | web | auto"""
        try:
            data = request.get_json(force=True) or {}
            mode = data.get("mode", "auto")
            if mode not in ("console", "web", "auto"):
                return jsonify({"ok": False, "error": "Invalid mode. Use: console, web, auto"}), 400
            sm = _sm()
            if sm is not None:
                sm.audio_mode = mode
            cfg_mgr.config["audio_mode"] = mode
            cfg_mgr.save()
            return jsonify({"ok": True, "audio_mode": mode})
        except Exception as exc:
            logger.error(f"[WebUI] set_audio_mode error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/logs/stream")
    def stream_logs():
        """SSE endpoint that streams latest Info and Debug logs."""
        from flask import Response, stream_with_context
        import time
        from datetime import datetime

        logger.debug("[WebUI-Logs] SSE Connection Request Received")

        def generate():
            # Get current log file paths (dynamic based on date)
            today = datetime.now().strftime('%Y-%m-%d')
            logs_dir = os.path.join(root_dir, "logs")
            info_path  = os.path.join(logs_dir, f"zentra_info_{today}.log")
            debug_path = os.path.join(logs_dir, f"zentra_debug_{today}.log")
            
            files = {
                'info':  {'path': info_path,  'pos': 0, 'label': 'INFO'},
                'debug': {'path': debug_path, 'pos': 0, 'label': 'DEBUG'}
            }

            # 1. SEND HISTORY (Last 50 lines per file)
            for k, f_info in files.items():
                if os.path.exists(f_info['path']):
                    try:
                        with open(f_info['path'], 'r', encoding='utf-8', errors='replace') as f:
                            lines = f.readlines()
                            f_info['pos'] = f.tell() # Mark current end
                            
                            # Send last 50 lines as history
                            for line in lines[-50:]:
                                if line.strip():
                                    data = json.dumps({
                                        "time":  "---", # Historical
                                        "level": f_info['label'],
                                        "text":  line.strip()
                                    })
                                    yield f"data: {data}\n\n"
                    except Exception as e:
                        logger.error(f"[WebUI] Log history error for {k}: {e}")

            # 2. POLL FOR NEW LINES
            while True:
                for k, f_info in files.items():
                    if not os.path.exists(f_info['path']):
                        continue
                    
                    try:
                        # Check if file was rotated or truncated
                        cur_size = os.path.getsize(f_info['path'])
                        if cur_size < f_info['pos']:
                            f_info['pos'] = 0 # reset
                        
                        with open(f_info['path'], 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(f_info['pos'])
                            new_lines = f.readlines()
                            f_info['pos'] = f.tell()
                            
                            for line in new_lines:
                                if line.strip():
                                    data = json.dumps({
                                        "time":  datetime.now().strftime("%H:%M:%S"),
                                        "level": f_info['label'],
                                        "text":  line.strip()
                                    })
                                    yield f"data: {data}\n\n"
                    except Exception as e:
                        pass # Ignore transient errors during rotation
                
                time.sleep(1) # Poll for new lines every second

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    @app.route("/api/events")
    def stream_events():
        from flask import Response, stream_with_context
        import time
        sm = _sm()
        
        def generate():
            while True:
                if sm and sm.detected_voice_command:
                    cmd = sm.detected_voice_command
                    sm.detected_voice_command = None # Consumer clears it
                    yield f"data: {json.dumps({'type': 'voice_detected', 'text': cmd})}\n\n"
                
                # We could add more event types here (e.g. state changes)
                time.sleep(0.1)
        
        return Response(stream_with_context(generate()), mimetype="text/event-stream")
