#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../.."

# Starts the Zentra Core System Tray Orchestrator quietly
python3 -m zentra.tray.tray_app &
disown
