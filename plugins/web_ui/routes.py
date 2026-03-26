import os
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
            
        ollama_models = list(cfg.get("backend", {}).get("ollama", {}).get("available_models", {}).values())
        personalita   = list(cfg.get("ai", {}).get("available_personalities", {}).values())
        cloud_models  = {
            p: cfg.get("llm", {}).get("providers", {}).get(p, {}).get("models", [])
            for p in ("openai", "anthropic", "groq", "gemini")
        }
        return jsonify({
            "piper_voices": onnx_files,
            "piper_dir":    piper_path_dir,
            "ollama_models": ollama_models,
            "personalities": personalita,
            "cloud_models":  cloud_models
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
            cfg_mgr.save()
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
            cfg_mgr.save()
            try:
                from core.processing import processore
                processore.configure(cfg_mgr.config)
            except Exception:
                pass
            return jsonify({"ok": True, "voice_status": new_val})
        except Exception as exc:
            logger.error(f"[WebUI] toggle_tts error: {exc}")
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
