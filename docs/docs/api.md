# API & Integration

Zentra Core provides several ways to integrate with external systems and extend its reaching.

## Bridge for Open WebUI
Zentra includes a bridge that allows it to act as a backend for [Open WebUI](https://openwebui.com/). 
- Use `zentra_webui_bridge.py` for real-time streaming support.
- Configurable through the central `config.json`.

## Home Assistant
Integrate with your smart home infrastructure via the bridge layer to control devices using natural language through Zentra.

## Developer Architecture
The modular core allows for direct Python-level integration:
- `core/cervello.py`: AI backend dispatcher (Ollama/Kobold).
- `core/processore.py`: Command execution and plugin coordination engine.
- `app/state_manager.py`: Thread-safe global state management.
