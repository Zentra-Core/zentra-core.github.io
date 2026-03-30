import os
import json
import threading
import time
from flask import request, jsonify

def init_audio_routes(app, cfg_mgr, root_dir, logger, get_sm=None):
    def _sm():
        return get_sm() if callable(get_sm) else get_sm

    # ── Audio Control API ─────────────────────────────────────────────────────

    @app.route("/api/audio/stop", methods=["POST"])
    def stop_audio():
        """Stop server-side TTS playback and generation."""
        try:
            # Stop playback and system-routing generation
            from core.audio.voice import stop_voice
            stop_voice()
            
            # Stop web-routing generation
            try:
                from plugins.web_ui.routes_chat import stop_voice_generation
                stop_voice_generation()
            except Exception as e:
                logger.debug(f"[WebUI] Could not stop web generation: {e}")

            logger.info("[WebUI] TTS stopped via API (ESC).")
            return jsonify({"ok": True})
        except Exception as exc:
            logger.error(f"[WebUI] stop_audio error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/toggle/mic", methods=["POST"])
    def toggle_mic():
        """Toggle listening_status — mirrors F4 on the console."""
        try:
            from core.audio.device_manager import get_audio_config, _save_audio_config
            acfg = get_audio_config()
            new_val = not acfg.get("listening_status", True)
            
            # Update live StateManager if present
            sm = _sm()
            if sm is not None:
                sm.listening_status = new_val
            
            acfg["listening_status"] = new_val
            if _save_audio_config(acfg):
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
            from core.audio.device_manager import get_audio_config, _save_audio_config
            acfg = get_audio_config()
            new_val = not acfg.get("voice_status", True)
            
            # Update live StateManager if present
            sm = _sm()
            if sm is not None:
                sm.voice_status = new_val
            
            acfg["voice_status"] = new_val
            if _save_audio_config(acfg):
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
            from core.audio.device_manager import get_audio_config, _save_audio_config
            acfg = get_audio_config()
            current_val = acfg.get("push_to_talk", False)
            new_val = not current_val
            
            acfg["push_to_talk"] = new_val
            if _save_audio_config(acfg):
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

    @app.route("/api/audio/test", methods=["POST"])
    def test_audio():
        """Tests the TTS engine (either local console or web preview)."""
        try:
            data = request.get_json(force=True) or {}
            text = data.get("text", "Test di Zentra Core, tutto funziona correttamente.")
            mode = data.get("mode", "console") # console or web
            
            from core.audio.device_manager import get_audio_config
            acfg = get_audio_config()

            if mode == "console":
                from core.audio.voice import speak
                # We force console playback
                threading.Thread(target=speak, args=(text,), daemon=True).start()
                return jsonify({"ok": True, "msg": "Speaking on console..."})
            
            else:
                from plugins.web_ui.routes_chat import generate_voice_file
                path = generate_voice_file(text, acfg)
                if path:
                    return jsonify({"ok": True, "url": f"/api/audio?t={int(time.time()*1000)}"})
                else:
                    return jsonify({"ok": False, "error": "Failed to generate audio file"})
                    
        except Exception as exc:
            logger.error(f"[WebUI] test_audio error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    # ── Audio Device Management API ───────────────────────────────────────────

    @app.route("/api/audio/devices", methods=["GET"])
    def get_audio_devices():
        """Returns available audio devices and current config_audio.json selection."""
        try:
            from core.audio.device_manager import list_devices, get_audio_config
            devices = list_devices()
            acfg = get_audio_config()
            return jsonify({
                "ok": True,
                "output_devices": devices["output"],
                "input_devices":  devices["input"],
                "selected_output_index": acfg.get("output_device_index", -1),
                "selected_output_name":  acfg.get("output_device_name",  ""),
                "selected_input_index":  acfg.get("input_device_index",  -1),
                "selected_input_name":   acfg.get("input_device_name",   ""),
                "last_scan":             acfg.get("last_scan",           ""),
            })
        except Exception as exc:
            logger.error(f"[WebUI] get_audio_devices error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/devices/scan", methods=["POST"])
    def scan_audio_devices():
        """Triggers device scan + beep test on the best output device."""
        try:
            from core.audio.device_manager import scan_and_select
            cfg = scan_and_select(verbose=False)
            return jsonify({
                "ok": True,
                "output_device_index": cfg.get("output_device_index", -1),
                "output_device_name":  cfg.get("output_device_name",  ""),
                "input_device_index":  cfg.get("input_device_index",  -1),
                "input_device_name":   cfg.get("input_device_name",   ""),
                "last_scan":           cfg.get("last_scan",           ""),
            })
        except Exception as exc:
            logger.error(f"[WebUI] scan_audio_devices error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/devices/select", methods=["POST"])
    def select_audio_device():
        """Manually sets output and/or input device index."""
        try:
            data = request.get_json(force=True) or {}
            from core.audio.device_manager import set_output_device, set_input_device, list_devices

            devs = list_devices()
            out_idx = data.get("output_index")
            in_idx  = data.get("input_index")

            if out_idx is not None:
                out_idx  = int(out_idx)
                out_name = next((d["name"] for d in devs["output"] if d["index"] == out_idx), "")
                set_output_device(out_idx, out_name)

            if in_idx is not None:
                in_idx  = int(in_idx)
                in_name = next((d["name"] for d in devs["input"] if d["index"] == in_idx), "")
                set_input_device(in_idx, in_name)

            return jsonify({"ok": True})
        except Exception as exc:
            logger.error(f"[WebUI] select_audio_device error: {exc}")
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.route("/api/audio/config", methods=["GET", "POST"])
    def manage_audio_config():
        """Gets or updates advanced audio settings in config_audio.json."""
        from core.audio.device_manager import get_audio_config, _save_audio_config
        
        if request.method == "GET":
            try:
                return jsonify({"ok": True, "config": get_audio_config()})
            except Exception as exc:
                return jsonify({"ok": False, "error": str(exc)}), 500
                
        if request.method == "POST":
            try:
                data = request.get_json(force=True) or {}
                cfg = get_audio_config()
                # Update allowed keys
                for k in ["voice_status", "listening_status", "piper_path", "onnx_model", 
                          "speed", "noise_scale", "noise_w", "sentence_silence",
                          "energy_threshold", "silence_timeout", "phrase_limit",
                          "input_device_index", "input_device_name", 
                          "output_device_index", "output_device_name",
                          "stt_source", "tts_destination"]:
                    if k in data:
                        cfg[k] = data[k]
                
                if "input_device_index" in data or "output_device_index" in data:
                    cfg["auto_select"] = False
                
                _save_audio_config(cfg)

                # Sync with running StateManager to prevent UI status from reverting
                sm = _sm()
                if sm:
                    if "stt_source" in data:
                        sm.stt_source = data["stt_source"]
                    if "tts_destination" in data:
                        sm.tts_destination = data["tts_destination"]

                return jsonify({"ok": True})
            except Exception as exc:
                logger.error(f"[WebUI] manage_audio_config POST error: {exc}")
                return jsonify({"ok": False, "error": str(exc)}), 500
