# Zentra Core v0.9.8 - Architecture Map

A visual guide to the Zentra Core folder structure and system components as of version 0.9.8.

```text
Zentra-Core/
│
├── app/                  # Application runtime environment
│   ├── application.py    # Main boot sequence and event loop
│   ├── bootstrapper.py   # System initialization (replaces inline logic)
│   ├── config.py         # Centralized ConfigManager (with Personality Sync)
│   ├── input_handler.py  # User keyboard and microphone unified input
│   ├── model_manager.py  # Global AI model state management
│   ├── personality_manager.py # F3 Selection & Dynamic Sync logic
│   ├── state_manager.py  # Tracks internal status (Thinking, Speaking, Ready)
│   └── threads.py        # Background asynchronous workers
│
├── core/                 # Low-level core engines
│   ├── audio/            # TTS (Piper) and STT voice systems
│   ├── i18n/             # Internationalization (IT/EN/ES)
│   ├── llm/              # Unified AI backends (Ollama, Kobold, Cloud)
│   │   └── vision/       # Multimodal adapters
│   ├── processing/       # Token streaming and filters
│   └── system/           # Bootstrap, versioning, and diagnostics
│
├── docs/                 # Operational manuals and technical documentation
│   ├── OPERATING_MANUAL.md
│   ├── TECHNICAL_GUIDE.md
│   └── zentra_core_structure_v0.9.8.md
│
├── logs/                 # Active system runtime and technical logs
│
├── memory/               # Persistent AI storage (SQLite)
│   ├── caveau/           # Long-term semantic memories
│   └── history/          # Conversation context
│
├── personality/          # AI Persona and Dynamic Prompts (.txt files)
│
├── plugins/              # Modular Plugin System
│   ├── dashboard/        # Hardware HUD
│   ├── domotica/         # IoT control
│   ├── executor/         # Shell execution
│   ├── file_manager/     # OS file operations
│   ├── help/             # Documentation assistant
│   ├── image_gen/        # AI Image Generation
│   ├── media/            # Audio/Video playback
│   ├── memory/           # Memory tools
│   ├── models/           # Real-time model macros
│   ├── roleplay/         # Advanced personas
│   ├── system/           # OS management
│   ├── web/              # Internet browsing
│   ├── web_ui/           # Native Web Interface (Full Plugin)
│   ├── webcam/           # Vision sensor
│   └── plugins_disabled/ # Inactive modules
│
├── .env                  # API Keys & Sensitive Data
├── config.json           # Master Configuration (Source of Truth)
├── main.py               # Application Entry Point
├── monitor.py            # Configuration Watchdog
└── zentra_proc_manager.py # Optional Process Manager
```

### Component Overview
* **`app/`**: Regulates the execution flow. `ConfigManager` now handles dynamic synchronization of personalities.
* **`core/`**: The engine room. Powered by **LiteLLM** for seamless switching between local (Ollama) and cloud backends.
* **`plugins/`**: Modular heart. Version 0.9.8 continues the Native Plugin architecture with improved stability and cleaner root structure.
* **`personality/`**: No longer requires manual config entry. Files added here are automatically detected and synced by the core.
