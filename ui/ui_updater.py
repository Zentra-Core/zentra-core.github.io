"""
MODULO: UI Updater - Zentra Core
DESCRIZIONE: Aggiorna la riga della dashboard hardware in-place ogni 2 secondi,
             senza flickering e senza interferire con l'input utente.
"""

import sys
import os
import time
import threading
import re
from colorama import Fore, Style
from ui import graphics
from core.system import plugin_loader
from ui.interface import get_hardware_row

# Blocco globale per proteggere l'accesso simultaneo allo stdout
stdout_lock = threading.Lock()

DASHBOARD_ROW = 3
_L = 90

_config_ref     = None
_state_ref      = None
_dashboard_mod  = None
_updater_active = False
_updater_thread = None

# --- Win32 API per il cursore (già presente nel tuo file, lo manteniamo)
if os.name == 'nt':
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.windll.kernel32
    STD_OUTPUT_HANDLE = -11
    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]
    class SMALL_RECT(ctypes.Structure):
        _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                    ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [("dwSize", COORD),
                    ("dwCursorPosition", COORD),
                    ("wAttributes", wintypes.WORD),
                    ("srWindow", SMALL_RECT),
                    ("dwMaximumWindowSize", COORD)]

def _update_dashboard_os(row_text, row_index):
    """
    Updates a specific row in the terminal using ANSI escape codes.
    Does not use Win32 APIs for positioning to avoid scrolling conflicts in large buffers.
    """
    # \0337: Save cursor position (DEC)
    # \033[{row_index};1H: Move to row;col
    # \033[2K: Clear current line
    # {row_text}: Write new content
    # \0338: Restore cursor position (DEC)
    sys.stdout.write(f"\0337\033[{row_index};1H\033[2K{row_text}\r\0338")
    sys.stdout.flush()

def _update_cycle(interval: float):
    global _updater_active
    while _updater_active:
        row = get_hardware_row(config=None, dashboard_mod=_dashboard_mod)
        if _updater_active:  # Double check before writing to video
            with stdout_lock:
                _update_dashboard_os(row, DASHBOARD_ROW)
        
        # Wait in small intervals to allow prompt termination
        for _ in range(int(interval * 10)):
            if not _updater_active:
                break
            time.sleep(0.1)

def start(config_manager, state_manager, dashboard_module, interval: float = 2.0):
    global _config_ref, _state_ref, _dashboard_mod, _updater_active, _updater_thread
    if _updater_active:
        return
    _config_ref    = config_manager
    _state_ref     = state_manager
    _dashboard_mod = dashboard_module
    _updater_active = True
    _updater_thread = threading.Thread(target=_update_cycle, args=(interval,), daemon=True, name="ZentraUIUpdater")
    _updater_thread.start()

def stop():
    global _updater_active, _updater_thread
    _updater_active = False
    if _updater_thread and _updater_thread.is_alive() and _updater_thread is not threading.current_thread():
# Wait a bit longer to be sure the dashboard thread kills itself completely 
# before opening panels like F7. This was causing a graphical glitch.
        _updater_thread.join(timeout=1.0)
    _updater_thread = None