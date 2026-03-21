# Plugin System

Zentra Core features a dynamic and modular plugin architecture. Every capability is a standalone module that can be enabled or disabled.

## Core Plugins

| Plugin | Description |
|--------|-------------|
| **System** | Execute shell commands and control OS. |
| **Web** | Search the web and open URLs. |
| **File Manager** | Explore and manage local files. |
| **Media** | Control system volume and playback. |
| **Dashboard** | Real-time hardware monitoring (CPU/RAM/GPU). |
| **Memory** | Persistent storage of conversations and preferences. |

## Creating Plugins
Developers can create custom plugins by adding new folders to the `plugins/` directory. Each plugin should follow the standard structure with a `main.py` entry point.
