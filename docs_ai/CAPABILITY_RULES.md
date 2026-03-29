# CAPABILITY RULES & DEFINITIONS

Definizione dei parametri e della struttura del sistema delle capacità.

## Struttura della Capability (JSON)

Ogni entry in `SYSTEM_CAPABILITIES.json` deve seguire questo schema:

```json
{
  "id": "identificativo_univoco",
  "description": "Spiegazione chiara di cosa fa",
  "risk": "low | medium | high",
  "available_in": ["cli", "web", "ai", "plugin"],
  "notes": "Dettagli tecnici o limitazioni"
}
```

## Livelli di Rischio

### 🔴 HIGH (Alto)
- Capacità che hanno accesso diretto al file system (scrittura/cancellazione).
- Capacità che eseguono comandi shell arbitrari.
- Capacità che gestiscono dati sensibili o credenziali.
*Esempi: EXECUTOR, FILE_MANAGER.*

### 🟡 MEDIUM (Medio)
- Capacità che modificano lo stato del sistema (reboot, reset memoria).
- Capacità che accedono a hardware periferico (Webcam, Microfono).
- Modifica delle configurazioni core.
*Esempi: WEBCAM, reboot_system, config_editor.*

### 🟢 LOW (Basso)
- Capacità puramente informative (Dashboard, Time, Weather).
- Interazioni sociali o di output (Personalità, TTS).
- Operazioni di sola lettura sicura.

## Regole di Sicurezza

1. **Sandboxing**: Le capacità ad alto rischio dovrebbero operare, dove possibile, entro cartelle specifiche (es. `data/`).
2. **User Confirmation**: Comandi distruttivi (Tabula Rasa) o pericolosi (Executor) dovrebbero richiedere una conferma utente, specialmente se invocati via AI.
3. **Visibility**: Lo stato di ogni capacità (Online/Offline) deve essere visibile nel registro centrale.

---

> [!NOTE]
> Queste regole servono a garantire che Zentra rimanga un assistente potente ma sicuro.
