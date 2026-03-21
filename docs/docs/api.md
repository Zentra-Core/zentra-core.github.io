# API & Integration

Zentra Core provides several ways to integrate with external systems.

## Bridge for Open WebUI
Zentra includes a bridge that allows it to act as a backend for [Open WebUI](https://openwebui.com/). 
- Use `zentra_webui_bridge.py` for streaming support.

## Home Assistant
Integrate with your smart home via the bridge layer to control devices using natural language.

## Developer API
The modular core allows for direct Python integration.
- `core/cervello.py`: AI backend dispatcher.
- `core/processore.py`: Command execution engine.
