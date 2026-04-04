# DEVELOPMENT RULES - Zentra Core

Regole tecniche per lo sviluppo del sistema standalone (Flask-based).

## Standard di Sviluppo

### 1. Registrazione Capabilities
Ogni modulo Python che introduce una nuova interazione deve essere accompagnato da un aggiornamento nei file `capabilities/*.json`.

### 2. Coding & Documentation Language (MANDATORY)
- **English Only:** Tutto il codice sorgente (classi, funzioni, variabili) e TUTTI i commenti nel codice devono essere scritti in inglese.
- **No Translation:** Non tradurre termini tecnici nella lingua della conversazione. Il codebase deve essere internazionalizzato.

### 3. Architettura a Plugin (Flask Blueprints)
Zentra non è più un bridge, ma un ecosistema nativo.
- Le interfacce Web (Chat, Config, Dashboard) devono essere sviluppate come **Flask Blueprints**.
- Ogni plugin deve trovarsi nella cartella `/plugins/` e registrare il proprio `web_bp` (Blueprint) nel sistema.

### 4. Integrità e Sincronizzazione
- Il sistema segue un'architettura dove il nucleo (`main.py`) comunica con i Blueprints.
- Lo stato del sistema (`StateManager`) deve essere sempre sincronizzato tra i diversi moduli web e il core.

### 5. Gestione Errori Web
- Ogni rotta Flask deve includere un blocco `try/except` che restituisca un errore loggato correttamente.
- Non far mai crashare il server principale per un errore in un plugin.

### 6. Configurazione Persistente (YAML + Pydantic)
- Il sistema ha deprecato `config.json` a favore di schemi **Pydantic v2** serializzati in `.yaml` all'interno della cartella `/config/`.
- Le modifiche alla configurazione devono sempre passare per il `ConfigManager`, che si occuperà in automatico della validazione dei tipi e del salvataggio nel giusto file YAML (`system.yaml`, `audio.yaml`, ecc.).
- Nessuna modifica raw va fatta al JSON storico.

---

> [!WARNING]
> La modifica del `plugin_loader.py` (Kernel) può compromettere l'intero ecosistema. Procedere con test isolati.