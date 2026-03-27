"""
Classe principale ConfigEditor che coordina il caricamento, l'editor e il salvataggio.
"""

import json
import os
from .locks import acquire_lock, release_lock
from .parameters import build_parameter_list
from .ui import UIManager
from core.i18n import translator

class ConfigEditor:
    def __init__(self, config_path="config.json"):
        # Ottieni il percorso della directory in cui si trova main.py
        script_dir = os.path.dirname(os.path.abspath(__file__))  # directory di core.py (ui/config_editor)
        ui_dir = os.path.dirname(script_dir)  # directory ui
        project_dir = os.path.dirname(ui_dir)  # directory del progetto (dove sta main.py)
        self.config_path = os.path.join(project_dir, config_path)
        self.config = self._load_config()
        self.param_list = build_parameter_list(self.config)
        self.modified = False

    def _load_config(self):
        """Carica il file JSON, pulisce config plugin vecchi e sincronizza con la cartella."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # --- Auto-sync plugins ---
            plugins_config = config.get("plugins", {})
            script_dir = os.path.dirname(os.path.abspath(__file__))  
            ui_dir = os.path.dirname(script_dir)  
            project_dir = os.path.dirname(ui_dir)  
            plugins_dir = os.path.join(project_dir, "plugins")
            
            # Find real plugins (folders with main.py or valid .py files)
            real_plugins = set()
            if os.path.exists(plugins_dir):
                for item in os.listdir(plugins_dir):
                    item_path = os.path.join(plugins_dir, item)
                    if os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, "main.py")):
                        real_plugins.add(item.upper())
                    elif os.path.isfile(item_path) and item.endswith(".py") and not item.startswith("_"):
                        real_plugins.add(item[:-3].upper())
            
            # Remove plugins from config.json that no longer exist
            to_remove = [p for p in plugins_config if p not in real_plugins]
            for p in to_remove:
                del plugins_config[p]
                self.modified = True  # Mark as modified if we cleaned something
                
            config["plugins"] = plugins_config
            
            # --- Auto-init Routing ---
            if "routing_engine" not in config:
                config["routing_engine"] = {"mode": "auto", "legacy_models": ""}
            elif "legacy_models" not in config["routing_engine"]:
                 config["routing_engine"]["legacy_models"] = ""
                 
            return config
            
        except Exception as e:
            print(f"Error loading {self.config_path}: {e}")
            raise

    def _save_config(self):
        """Salva il file JSON se ci sono modifiche e aggiorna il traduttore."""
        if self.modified:
            try:
                # Check language change before saving
                old_language = None
                if os.path.exists(self.config_path):
                    try:
                        with open(self.config_path, 'r', encoding='utf-8') as f:
                            old_data = json.load(f)
                            old_language = old_data.get("language")
                    except: pass

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                
                # Sync translator if language changed
                new_language = self.config.get("language")
                if new_language and new_language != old_language:
                    from core.i18n import translator
                    translator.get_translator().set_language(new_language)
                
                print(f"\n{translator.t('config_saved_success')}")
            except Exception as e:
                print(f"\n{translator.t('config_save_error', error=str(e))}")

    def _get_value(self, param):
        """Returns a parameter value from current config."""
        try:
            # Determine active backend
            backend_type = self.config.get('backend', {}).get('type', 'ollama')
            backend_config = self.config.get('backend', {}).get(backend_type, {})
            
            # Key is already present in param.key
            key = param.key
            
            # Handle different section types
            if param.section == 'backend':
                return backend_config.get(key)
            elif param.section == 'ollama':
                return self.config.get('backend', {}).get('ollama', {}).get(key)
            elif param.section == 'kobold':
                return self.config.get('backend', {}).get('kobold', {}).get(key)
            elif param.section == 'voice':
                return self.config.get('voice', {}).get(key)
            elif param.section == 'ai':
                return self.config.get('ai', {}).get(key)
            elif param.section == 'bridge':
                return self.config.get('bridge', {}).get(key)
            elif param.section == 'listening':
                return self.config.get('listening', {}).get(key)
            elif param.section == 'filters':
                return self.config.get('filters', {}).get(key)
            elif param.section == 'logging':
                return self.config.get('logging', {}).get(key)
            elif param.section == 'system':
                return self.config.get(key)
            elif param.section == 'llm':
                return self.config.get('llm', {}).get(key)
            elif param.section.startswith('llm_'):
                provider = param.section.split('_')[1]
                return self.config.get('llm', {}).get('providers', {}).get(provider, {}).get(key)
            elif param.section == 'plugin':
                # Plugin section: access config['plugins'][param.plugin_tag][key]
                plugins = self.config.get('plugins', {})
                plugin_cfg = plugins.get(param.plugin_tag, {})
                return plugin_cfg.get(key)
            elif param.section == 'routing_engine':
                return self.config.get('routing_engine', {}).get(key)
            elif param.section.startswith('legacy_'):
                # Value is True if key (model name) is in CSV string
                legacy_str = self.config.get('routing_engine', {}).get('legacy_models', '')
                legacy_list = [m.strip().lower() for m in legacy_str.split(',') if m.strip()]
                return key.lower() in legacy_list
            else:
                return None
        except Exception as e:
            print(f"Error in _get_value for {param.label}: {e}")
            return None

    def _set_value(self, param, value):
        """Imposta il valore e marca come modificato."""
        try:
            # Determina il backend attivo
            backend_type = self.config.get('backend', {}).get('type', 'ollama')
            
            # Uso diretto di param.key
            key = param.key
            
            # Gestisci i diversi tipi di sezioni
            if param.section == 'backend':
                if backend_type not in self.config['backend']:
                    self.config['backend'][backend_type] = {}
                old = self.config['backend'][backend_type].get(key)
                if old != value:
                    self.config['backend'][backend_type][key] = value
                    self.modified = True
            elif param.section == 'ollama':
                if 'ollama' not in self.config['backend']:
                    self.config['backend']['ollama'] = {}
                old = self.config['backend']['ollama'].get(key)
                if old != value:
                    self.config['backend']['ollama'][key] = value
                    self.modified = True
            elif param.section == 'kobold':
                if 'kobold' not in self.config['backend']:
                    self.config['backend']['kobold'] = {}
                old = self.config['backend']['kobold'].get(key)
                if old != value:
                    self.config['backend']['kobold'][key] = value
                    self.modified = True
            elif param.section == 'voice':
                if 'voice' not in self.config:
                    self.config['voice'] = {}
                old = self.config['voice'].get(key)
                if old != value:
                    self.config['voice'][key] = value
                    self.modified = True
            elif param.section == 'ai':
                if 'ai' not in self.config:
                    self.config['ai'] = {}
                old = self.config['ai'].get(key)
                if old != value:
                    self.config['ai'][key] = value
                    self.modified = True
            elif param.section == 'bridge':
                if 'bridge' not in self.config:
                    self.config['bridge'] = {}
                old = self.config['bridge'].get(key)
                if old != value:
                    self.config['bridge'][key] = value
                    self.modified = True
            elif param.section == 'listening':
                if 'listening' not in self.config:
                    self.config['listening'] = {}
                old = self.config['listening'].get(key)
                if old != value:
                    self.config['listening'][key] = value
                    self.modified = True
            elif param.section == 'filters':
                if 'filters' not in self.config:
                    self.config['filters'] = {}
                old = self.config['filters'].get(key)
                if old != value:
                    self.config['filters'][key] = value
                    self.modified = True
            elif param.section == 'logging':
                if 'logging' not in self.config:
                    self.config['logging'] = {}
                old = self.config['logging'].get(key)
                if old != value:
                    self.config['logging'][key] = value
                    self.modified = True
            elif param.section == 'system':
                old = self.config.get(key)
                if old != value:
                    self.config[key] = value
                    self.modified = True
            elif param.section == 'llm':
                if 'llm' not in self.config:
                    self.config['llm'] = {}
                old = self.config['llm'].get(key)
                if old != value:
                    self.config['llm'][key] = value
                    self.modified = True
            elif param.section.startswith('llm_'):
                provider = param.section.split('_')[1]
                if 'llm' not in self.config: self.config['llm'] = {}
                if 'providers' not in self.config['llm']: self.config['llm']['providers'] = {}
                if provider not in self.config['llm']['providers']: self.config['llm']['providers'][provider] = {}
                
                old = self.config['llm']['providers'][provider].get(key)
                if old != value:
                    self.config['llm']['providers'][provider][key] = value
                    self.modified = True
            elif param.section == 'plugin':
                # Sezione plugin: aggiorna config['plugins'][param.plugin_tag][key]
                if 'plugins' not in self.config:
                    self.config['plugins'] = {}
                if param.plugin_tag not in self.config['plugins']:
                    self.config['plugins'][param.plugin_tag] = {}
                old = self.config['plugins'][param.plugin_tag].get(key)
                if old != value:
                    self.config['plugins'][param.plugin_tag][key] = value
                    self.modified = True
            elif param.section == 'routing_engine':
                if 'routing_engine' not in self.config:
                    self.config['routing_engine'] = {}
                old = self.config['routing_engine'].get(key)
                if old != value:
                    self.config['routing_engine'][key] = value
                    self.modified = True
            elif param.section.startswith('legacy_'):
                # Sincronizza il boolean con la stringa legacy_models
                if 'routing_engine' not in self.config:
                    self.config['routing_engine'] = {"legacy_models": ""}
                
                legacy_str = self.config['routing_engine'].get('legacy_models', '')
                legacy_list = [m.strip().lower() for m in legacy_str.split(',') if m.strip()]
                
                model_name = key.lower()
                if value: # Aggiungi
                    if model_name not in legacy_list:
                        legacy_list.append(model_name)
                        self.config['routing_engine']['legacy_models'] = ", ".join(legacy_list)
                        self.modified = True
                else: # Rimuovi
                    if model_name in legacy_list:
                        legacy_list.remove(model_name)
                        self.config['routing_engine']['legacy_models'] = ", ".join(legacy_list)
                        self.modified = True
        except Exception as e:
            print(f"Errore in _set_value per {param.label}: {e}")

    def run(self):
        """Avvia l'editor interattivo con lock."""
        if not acquire_lock():
            print("Impossibile acquisire il lock. Editor già in esecuzione?")
            return
        
        try:
            result = None
            ui = UIManager(self.param_list, self._get_value, self._set_value)
            result = ui.run()
            
            import sys
            import time
            from core.i18n import translator
            
            if result == "REBOOT":
                if self.modified:
                    self._save_config()
                print(f"\n\033[91m{translator.t('rebooting_msg')}\033[0m")
                time.sleep(1)
                sys.exit(42)
                
            elif result == "SAVE":
                import os
                # Pulisce lo schermo per chiarezza per il report esito testuale
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\n\n\033[92m{'═'*55}")
                print("   ✅ CONFIGURAZIONE SALVATA CON SUCCESSO!   ")
                print(f"{'═'*55}\033[0m")
                
                if self.modified:
                    self._save_config()
                
                # Auto-riavvio garantito per applicare le modifiche
                print(f"\n\033[93m{translator.t('rebooting_msg')}...\033[0m")
                time.sleep(2)
                sys.exit(42)
                
            elif result == "DISCARD":
                print(f"\n\033[93mUscita senza salvare. Le modifiche sono state scartate.\033[0m")
                # Nessun salvataggio, nessun riavvio
                
            else: # NO_CHANGES
                # Possiamo salvare solo se core.py ha pulito vecchi plugin, ma non serve riavviare
                if self.modified:
                    self._save_config()
                    
        finally:
            release_lock()