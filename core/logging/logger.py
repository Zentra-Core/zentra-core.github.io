import logging
import os
import sys
import subprocess
from datetime import datetime

# Disabilita i debug di requests e urllib3 (troppo verbosi)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Creiamo la cartella log se non esiste
if not os.path.exists("logs"):
    os.makedirs("logs")

# Nome del file basato sulla data odierna per una rotazione giornaliera
log_filename = f"logs/aura_{datetime.now().strftime('%Y-%m-%d')}.log"

logger = logging.getLogger("AuraLogger")
logger.setLevel(logging.DEBUG)  # Il logger accetta tutto

# Svuota gli handler esistenti se modulo ricaricato
if logger.hasHandlers():
    logger.handlers.clear()

# Handler per il file (registra TUTTO, livello DEBUG)
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(file_formatter)

# Handler per la console (default INFO)
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: '\033[96m',    # Ciano
        logging.INFO: '\033[97m',     # Bianco
        logging.WARNING: '\033[93m',  # Giallo
        logging.ERROR: '\033[91m',    # Rosso
        logging.CRITICAL: '\033[95m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = ColorFormatter('%(asctime)s [%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)

# Aggiungi gli handler al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

_console_window_started = False

def init_logger(config):
    """
    Inizializza le impostazioni di logging lette da config.json
    """
    global _console_window_started
    
    logging_config = config.get('logging', {})
    
    if not logging_config:
        # Se non c'è, mettiamo i default e poi config_manager lo salverà in futuro
        pass
        
    destinazione = logging_config.get('destinazione', 'chat')
    livello_str = logging_config.get('livello', 'INFO').upper()
    
    livello = getattr(logging, livello_str, logging.INFO)
    
    # Aggiorna il livello per visualizzare più o meno dettagli (DEBUG, INFO, WARNING, ERROR)
    console_handler.setLevel(livello)
    
    if destinazione == 'console':
        # Disabilita l'output sulla chat principale rimuovendo console_handler
        if console_handler in logger.handlers:
            logger.removeHandler(console_handler)
        
        # Apri la console separata solo una volta
        if not _console_window_started:
            # Usa PowerShell per simulare 'tail -f' con colorazione automatica real-time
            ps_script = (
                f"Get-Content -Path '{log_filename}' -Wait -Tail 20 | ForEach-Object {{ "
                "if ($_ -match '\\[ERROR\\]') { Write-Host $_ -ForegroundColor Red } "
                "elseif ($_ -match '\\[WARNING\\]') { Write-Host $_ -ForegroundColor Yellow } "
                "elseif ($_ -match '\\[DEBUG\\]') { Write-Host $_ -ForegroundColor Cyan } "
                "else { Write-Host $_ -ForegroundColor White } "
                "}"  # Singola parentesi graffa finale per chiudere ForEach-Object
            )
            subprocess.Popen(f'start powershell -NoExit -Command "{ps_script}"', shell=True)
            _console_window_started = True
    else:
        # Assicurati che l'output standard sia attivo
        if console_handler not in logger.handlers:
            logger.addHandler(console_handler)


def info(messaggio):
    """Registra un evento informativo standard."""
    logger.info(messaggio)

def errore(messaggio):
    """Registra un errore critico nel sistema."""
    logger.error(messaggio)

def debug(modulo, messaggio):
    """Registra un messaggio di debug nel file di log (non appare in console se livello=INFO)."""
    logger.debug(f"[DEBUG][{modulo}] {messaggio}")
    
def warning(modulo, messaggio):
    """Registra un avviso (warning)."""
    logger.warning(f"[WARNING][{modulo}] {messaggio}")

def debug_ia(testo_utente, risposta_ia, tag_rilevato=None):
    """
    Registra il flusso completo della conversazione e l'attivazione dei plugin.
    Utile per capire se l'IA sta formattando correttamente i tag.
    """
    info_tag = f" | TAG RILEVATO: {tag_rilevato}" if tag_rilevato else ""
    logger.info(f"UTENTE: {testo_utente} | IA: {risposta_ia}{info_tag}")

def leggi_log(n=10, solo_errori=False):
    """
    Ritorna le ultime N righe del log. 
    Se solo_errori è True, filtra solo le righe critiche.
    """
    try:
        if not os.path.exists(log_filename):
            return "Nessun log trovato per la giornata odierna."
            
        with open(log_filename, 'r', encoding='utf-8') as f:
            righe = f.readlines()
            if solo_errori:
                righe = [r for r in righe if "[ERROR]" in r]
            
            ultime_righe = righe[-n:]
            return "".join(ultime_righe) if ultime_righe else "Il registro è vuoto."
    except Exception as e:
        return f"Errore durante la lettura del file log: {e}"
