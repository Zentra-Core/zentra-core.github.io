#!/bin/bash
echo "=================================================="
echo "  ZENTRA CORE - ENABLE TRAY AUTOSTART (LINUX)"
echo "=================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZENTRA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TRAY_RUNNER="$ZENTRA_ROOT/scripts/linux/run/ZENTRA_TRAY_LINUX.sh"

if [ ! -f "$TRAY_RUNNER" ]; then
    echo "[!] ERROR: Could not find ZENTRA_TRAY_LINUX.sh at:"
    echo "    $TRAY_RUNNER"
    exit 1
fi

chmod +x "$TRAY_RUNNER"

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
DESKTOP_FILE="$AUTOSTART_DIR/zentra-core-tray.desktop"

echo "[*] Writing XDG Desktop Entry..."
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Exec=bash "$TRAY_RUNNER"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Zentra Core
Comment=Zentra Core Agentic OS Tray
Icon=$ZENTRA_ROOT/zentra/assets/Zentra_Core_Logo_NBG.png
Terminal=false
EOF

chmod +x "$DESKTOP_FILE"

echo ""
echo "[+] Done! Zentra Tray natively added to Linux autostart."
echo "    Path: $DESKTOP_FILE"
echo ""
