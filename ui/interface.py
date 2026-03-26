"""
MODULO: Interface & UI - Zentra Core v0.6
DESCRIZIONE: Gestisce la UI del terminale, le dashboard hardware e i tasti funzione.

"Nello specifico: Disegna la barra blu di stato (modello, voce, anima) e la barra 
centrale che si collega a plugins.dashboard per i dati hardware reali. Gestisce 
inoltre l'intercettazione dei tasti funzione (F1-F6) per i menu rapidi."
"""

import os
import sys
import msvcrt
import json
import threading
import time
import glob
import requests
import psutil  # Necessario per fallback telemetria
try:
    import GPUtil  # Telemetria GPU/VRAM
except ImportError:
    GPUtil = None
from ui import graphics
from colorama import init, Fore, Back, Style
from core.system import plugin_loader, version
from core.system.version import get_version_string
from core.i18n import translator

# "Inizializzazione Colorama per colori ANSI e sfondi su Windows"
init(convert=True, autoreset=True)

# Global variable for animation control
animation_active = False

# Standard color palette
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
CYAN = Fore.CYAN
MAGENTA = Fore.MAGENTA
WHITE = Fore.WHITE
RESET = Style.RESET_ALL

def translate_status(s):
    """Translates known status keys using the translator."""
    if not s:
        return s
    s_lower = s.lower()
    keys = ["ready", "error", "offline", "timeout", "waiting", "loading", "online", "disabled"]
    for k in keys:
        if s_lower.startswith(k):
            remainder = s[len(k):]
            return translator.t(k) + remainder
    return s

def get_status_color(s):
    """Returns the Fore color code based on current status."""
    if not s:
        return Fore.WHITE
    s_lower = s.lower()
    
    # Status -> color mapping
    if "ready" in s_lower or "pronto" in s_lower or "online" in s_lower:
        return Fore.GREEN
    if "thinking" in s_lower or "pensando" in s_lower or "loading" in s_lower:
        return Fore.YELLOW
    if "speaking" in s_lower or "parlando" in s_lower:
        return Fore.CYAN
    if "error" in s_lower or "offline" in s_lower:
        return Fore.RED
        
    return Fore.WHITE

def setup_console():
    """Cleans screen and forces UTF-8."""
    if sys.platform == 'win32':
        os.system('chcp 65001 > nul')
    # Reset scrolling region and clear screen
    sys.stdout.write("\033[r")
    os.system('cls' if os.name == 'nt' else 'clear')

def check_ollama():
    """Checks if Ollama server is active for the status bar."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=0.2)
        return r.status_code == 200
    except:
        return False

def show_complete_ui(config, voice_status, listening_status, system_status="READY"):
    """ Draws the complete interface: Blue Bar (Status), Hardware Bar (placeholder) and Footer.
        The hardware bar will be updated in real-time by ui_updater.
    """
    setup_console()
    
    # MODIFIED: Reads model from active backend with automatic fallback
    from app.model_manager import ModelManager
    backend_type, model = ModelManager.get_effective_model_info(config)
    
    soul = config.get('ai', {}).get('active_personality', 'N/D').replace('.txt', '')
    mic = "ON" if listening_status else "OFF"
    spk = "ON" if voice_status else "OFF"
    
    L = 90  # Larghezza fissa per l'allineamento
    
    # 1. BARRA SUPERIORE (TITOLO) - NERO VERO
    titolo = translator.t("welcome", version=version.VERSION).center(L)
    print(f"\033[46m\033[30m{titolo}\033[0m")
    
    # 2. DYNAMIC STATUS BAR
    mic_str = "ON" if listening_status else f"{Fore.RED}OFF{Fore.WHITE}"
    mic_len = 2 if listening_status else 3
    spk_str = "ON" if voice_status else f"{Fore.RED}OFF{Fore.WHITE}"
    spk_len = 2 if voice_status else 3
    
    # Attempts to translate status if it's a known key, otherwise uses as is
    status_translated = translate_status(system_status)
    status_color = get_status_color(system_status)
    
    # Create status string with its color
    info_status_raw = translator.t("system_status", status="{ST_PLACEHOLDER}")
    info_status = info_status_raw.replace("{ST_PLACEHOLDER}", f"{status_color}{status_translated}{Fore.WHITE}")
    
    # Calcolo lunghezza visibile per il padding
    header_mod = translator.t("header_model")
    header_ani = translator.t("header_soul")
    header_mic = translator.t("header_mic")
    header_voc = translator.t("header_voice")
    
    # Visible length (without color codes)
    visible_status_text = translator.t("system_status", status=status_translated)
    visible_len = len(f" {visible_status_text} | {header_mod}: {model} | {header_ani}: {soul} | {header_mic}:  | {header_voc}:  ") + mic_len + spk_len
    pad_left = max(0, L - visible_len) // 2
    pad_right = max(0, L - visible_len) - pad_left
    
    info_status_colored = f" {info_status} | {header_mod}: {model} | {header_ani}: {soul} | {header_mic}: {mic_str} | {header_voc}: {spk_str} "
    print(f"{Back.BLUE}{Fore.WHITE}{' '*pad_left}{info_status_colored}{' '*pad_right}{Style.RESET_ALL}")
    
    # 3. HARDWARE BAR (DYNAMIC)
    hw_row = get_hardware_row(config, dashboard_mod=None)
    print(hw_row)
    
    # 4. FOOTER COMANDI RAPIDI
    print(f"{Fore.CYAN}{'━' * L}{Style.RESET_ALL}")
    comandi = (
        f" {translator.t('menu_help')} | {translator.t('menu_models')} | "
        f"{translator.t('menu_persona')} | {translator.t('menu_mic')} | "
        f"{translator.t('menu_voice')} | {translator.t('menu_reboot')} | "
        f"{translator.t('menu_config')} | {translator.t('menu_exit')} "
    )
    print(f"{Style.DIM}{comandi.center(L)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'━' * L}{Style.RESET_ALL}")
    
    # 5. IMPOSTAZIONE AREA DI SCROLLING (Dalla riga 7 alla fine)
    # Questo blocca le prime 6 righe in alto, impedendo che scorrano via.
    sys.stdout.write("\033[7;r")
    # Posiziona il cursore alla riga 7 (inizio area chat)
    sys.stdout.write("\033[7;1H")
    sys.stdout.flush()
    
def get_hardware_row(config=None, dashboard_mod=None):
    """
    Returns the formatted string for the hardware row (CPU, RAM, VRAM, backend).
    Guarantees a fixed length of 90 characters to avoid UI corruption/wrap.
    """
    import re
    L = 90
    
    if dashboard_mod is None:
        dashboard_mod = plugin_loader.get_plugin_module("DASHBOARD")
    
    if dashboard_mod:
        try:
            stats = dashboard_mod.get_stats()
            cpu = stats['cpu']
            ram = stats['ram']
            vram = stats['vram']
            if len(str(vram)) > 25: vram = str(vram)[:22] + ".."
            backend_status = stats['backend_status']
            
            cpu_bar = graphics.create_bar(cpu, width=5)
            ram_bar = graphics.create_bar(ram, width=5)
            
            # Translate backend status
            if backend_status in ("READY", "CLOUD", "ONLINE"):
                display_status = translator.t("ready")
                if backend_status == "CLOUD": display_status = "CLOUD"
                status_color = Fore.GREEN
            elif backend_status in ("OFFLINE", "ERROR", "TIMEOUT"):
                key = backend_status.lower() if backend_status.lower() in ["offline", "error", "timeout"] else "disabled"
                display_status = translator.t(key)
                status_color = Fore.RED
            elif backend_status == "STARTING":
                display_status = "STARTING..."
                status_color = Fore.YELLOW
            else:
                display_status = backend_status if backend_status else "--"
                status_color = Fore.YELLOW

            info_hw = translator.t("hardware_line", 
                cpu=cpu_bar, ram=ram_bar, gpu=stats.get('gpu_load', 'N/D'), vram=vram, 
                backend=f"{status_color}{display_status}{Style.RESET_ALL}"
            )
        except Exception as e:
            info_hw = f"{Fore.RED}-- HARDWARE ERROR: {e} --{Style.RESET_ALL}"
    else:
        # Se il plugin è disabilitato, restituiamo una riga vuota di 90 spazi
        return f"{Fore.CYAN}{' ' * L}{Style.RESET_ALL}"
    
    # Explicitly truncate to avoid wrap-induced scrolling
    # We limit the visible characters, ANSI codes are extra.
    # A simple but effective way: ensure the text doesn't exceed a safe width.
    return f"{Fore.CYAN}{info_hw[:500]}{Style.RESET_ALL}"

def update_status_bar_in_place(config, voice_status, listening_status, system_status="READY"):
    """Updates only row 2 (Status Bar) without clearing the screen."""
    from ui.ui_updater import _update_dashboard_os, stdout_lock
    from colorama import Back, Fore, Style
    from app.model_manager import ModelManager
    
    backend_type, model = ModelManager.get_effective_model_info(config)
    soul = config.get('ai', {}).get('active_personality', 'N/D').replace('.txt', '')
    
    mic_str = "ON" if listening_status else f"{Fore.RED}OFF{Fore.WHITE}"
    mic_len = 2 if listening_status else 3
    spk_str = "ON" if voice_status else f"{Fore.RED}OFF{Fore.WHITE}"
    spk_len = 2 if voice_status else 3
    
    L = 90
    status_translated = translate_status(system_status)
    status_color = get_status_color(system_status)
    
    info_status_raw = translator.t("system_status", status="{ST_PLACEHOLDER}")
    info_status = info_status_raw.replace("{ST_PLACEHOLDER}", f"{status_color}{status_translated}{Fore.WHITE}")
    
    header_mod = translator.t("header_model")
    header_ani = translator.t("header_soul")
    header_mic = translator.t("header_mic")
    header_voc = translator.t("header_voice")
    
    visible_status_text = translator.t("system_status", status=status_translated)
    visible_len = len(f" {visible_status_text} | {header_mod}: {model} | {header_ani}: {soul} | {header_mic}:  | {header_voc}:  ") + mic_len + spk_len
    pad_left = max(0, L - visible_len) // 2
    pad_right = max(0, L - visible_len) - pad_left
    
    info_status_colored = f" {info_status} | {header_mod}: {model} | {header_ani}: {soul} | {header_mic}: {mic_str} | {header_voc}: {spk_str} "
    formatted_row = f"{Back.BLUE}{Fore.WHITE}{' '*pad_left}{info_status_colored}{' '*pad_right}{Style.RESET_ALL}"
    
    with stdout_lock:
        _update_dashboard_os(formatted_row, 2)

    
def show_models_menu(categorized_models, current):
    """Prints the selection for LLM models with categorized blue sections."""
    from app.model_manager import ModelManager
    
    t_title = translator.t('model_mgmt_title')
    L = 58
    
    print(f"\n{CYAN}╔{'═' * (L)}╗{RESET}")
    print(f"{CYAN}║{WHITE} {t_title.center(L-2)} {CYAN}║{RESET}")
    print(f"{CYAN}╠{'═' * (L)}╣{RESET}")
    
    # Try to get model sizes for Ollama
    model_sizes = {}
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=1)
        if resp.status_code == 200:
            for m in resp.json().get('models', []):
                name = m.get('name', '')
                size = m.get('size', 0)
                if size > 1024**3:
                    model_sizes[name] = f"{size/(1024**3):.1f}GB"
                elif size > 1024**2:
                    model_sizes[name] = f"{size/(1024**2):.0f}MB"
    except:
        pass
    
    global_idx = 1
    for category, models in categorized_models.items():
        # Blue category header bar
        cat_title = f" ── {category.upper()} ── "
        print(f"{CYAN}║{Back.BLUE}{Fore.WHITE}{cat_title.center(L)}{Style.RESET_ALL}{CYAN}║{RESET}")
        print(f"{CYAN}║{'─' * (L)}║{RESET}")
        
        for m in models:
            is_active = m == current
            pref = f"{GREEN} ► " if is_active else "   "
            size_str = ""
            if category == "Ollama (Local)" and m in model_sizes:
                size_str = f"  {YELLOW}[{model_sizes[m]}]{RESET}"
            
            model_str = f"{CYAN}║{RESET} {pref}{global_idx:2}. {m}{size_str}"
            print(model_str)
            global_idx += 1
        
        print(f"{CYAN}║{RESET}")  # Blank separator line between categories
            
    print(f"{CYAN}╚{'═' * (L)}╝{RESET}")
    print(f"{YELLOW}  {translator.t('select_model_index')}{RESET}")




def show_personality_menu(file_list, current):
    """Prints the selection for personality TXT files."""
    head = translator.t("select_personality")
    print(f"\n{MAGENTA}{head}{RESET}")
    for i, f in enumerate(file_list, 1):
        pref = f"{GREEN} >> " if f == current else "    "
        print(f"{pref}{i}. {f.replace('.txt', '')}{RESET}")
    print(f"{MAGENTA}{'═' * len(head)}{RESET}")
    print(f"{YELLOW}{translator.t('help_footer')}{RESET}")

def show_help():
    """Displays the dynamic guide generated by the plugin scanner."""
    from core.system.plugin_loader import generate_dynamic_guide
    
    # Clear the screen to make space for the extended guide
    setup_console()
    
    # Centered Header
    header_text = f"{CYAN}╔════════════════ {translator.t('help_title')} ════════════════╗{RESET}"
    print(f"\n{header_text.center(90)}")
    print(f"{WHITE}{translator.t('help_scanning')}{RESET}".center(90))
    print()
    
    try:
        data = generate_dynamic_guide()
        if not data:
            print(f"{RED}{translator.t('help_no_modules')}{RESET}".center(90))
        else:
            for item in data:
                tag = item['tag']
                status_text = item['status']
                desc = item['description']
                commands = item.get('commands', {})
                example = item.get('example', '')
                
                # Color variations for disabled modules
                if status_text in ("ACTIVE", "ATTIVO", "ONLINE"):
                    status_col = GREEN
                    border = CYAN
                else:
                    status_col = RED
                    border = Fore.LIGHTBLACK_EX
                    
                print(f"{border}├─ {status_col}[{tag.upper()}] {RESET}- {translator.t('system_status', status=status_col+status_text+RESET)}")
                print(f"{border}│{RESET}  {WHITE}{translator.t('help_role')}{RESET} {desc}")
                
                if commands:
                    print(f"{border}│{RESET}  {YELLOW}{translator.t('help_commands')}{RESET}")
                    for cmd, explanation in commands.items():
                        print(f"{border}│{RESET}    • {cmd} -> {explanation}")
                        
                if example:
                    print(f"{border}│{RESET}  {MAGENTA}{translator.t('help_example')}{RESET} {Fore.WHITE}'{example}'{RESET}")
                    
                print(f"{border}│{RESET}")
                
    except Exception as e:
        print(f"{RED}Fatal error generating dynamic guide: {e}{RESET}")
        
    closure = f"{CYAN}╚════════════════════════════════════════════════════════════╝{RESET}"
    print(f"{closure.center(90)}")
    print(f"\n{YELLOW}{translator.t('help_footer')}{RESET}".center(90))
    
    # Flush old keystrokes before blocking
    while msvcrt.kbhit(): msvcrt.getch()
    msvcrt.getch()
    # Clean up on exit and leave the task to show_complete_ui
    setup_console()

def write_zentra(text):
    """Prints Zentra's response highlighting it in CYAN."""
    from core.processing import filtri
    # Ensure terminal safety
    text = filtri.clean_for_video(text)
    print(Fore.CYAN + "ZENTRA: " + Style.RESET_ALL + text)
    
def read_keyboard_input(prefix, current_input):
    if msvcrt.kbhit():
        ch_raw = msvcrt.getch()
        # Function keys F1-F6
        if ch_raw in [b'\x00', b'\xe0']:
            special_key = msvcrt.getch()
            if special_key == b';': return "F1", current_input
            if special_key == b'<': return "F2", current_input
            if special_key == b'=': return "F3", current_input
            if special_key == b'>': return "F4", current_input
            if special_key == b'?': return "F5", current_input
            if special_key == b'@': return "F6", current_input
            if special_key == b'A': return "F7", current_input
            # Optional: add F8-F12 if desired
            # if special_key == b'B': return "F8", current_input
            # if special_key == b'C': return "F9", current_input
            # if special_key == b'D': return "F10", current_input
            # if special_key == b'E': return "F11", current_input
            # if special_key == b'F': return "F12", current_input
            return None, current_input

        if ch_raw == b'\x1b':  # ESC
            if current_input:
                return "CLEAR", ""       # clear all
            else:
                return "ESC", current_input   # otherwise exit

        try: ch = ch_raw.decode('utf-8')
        except: return None, current_input

        if ch == '\r': return "ENTER", current_input
        elif ch == '\b':
            if len(current_input) > 0:
                current_input = current_input[:-1]
                sys.stdout.write('\b \b')
                sys.stdout.flush()
            return "CHAR", current_input
        else:
            current_input += ch
            sys.stdout.write(ch)
            sys.stdout.flush()
            return "CHAR", current_input

    return None, current_input

# --- DOTS ANIMATION LOGIC ---

def _dots_cycle():
    """Shows only animated dots without text."""
    global animation_active
    phases = [".  ", ".. ", "...", ".. "] 
    idx = 0
    sys.stdout.write(YELLOW) 
    while animation_active:
        sys.stdout.write(f"\r{phases[idx % len(phases)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.3)

def start_thinking():
    """Launches the animation in a separate thread."""
    global animation_active
    if not animation_active:
        animation_active = True
        t = threading.Thread(target=_dots_cycle, daemon=True)
        t.start()

def stop_thinking():
    """Stops the dots animation."""
    global animation_active
    animation_active = False
    sys.stdout.write(f"\r   \r{RESET}")
    sys.stdout.flush()
    
def list_personalities():
    """Scans the personality folder to find real .txt files."""
    folder = "personality"
    if not os.path.exists(folder): os.makedirs(folder)
    return [os.path.basename(f) for f in glob.glob(os.path.join(folder, "*.txt"))]

def show_soul_menu(available_souls):
    """Shows a menu for personality selection."""
    print(f"\n{CYAN}=== SYSTEM SOUL SELECTION ==={RESET}")
    for i, name in enumerate(available_souls, 1):
        print(f"{YELLOW}{i}{RESET} - {name}")
    print(f"{CYAN}================================{RESET}")
    sys.stdout.write(f"{GREEN}{translator.t('select_persona_index')}{RESET}")
    sys.stdout.flush()