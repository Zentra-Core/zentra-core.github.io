import speech_recognition as sr
from . import voice
from core.logging import logger
import json
import time

try:
    import keyboard
except ImportError:
    keyboard = None

def listen(state=None):
    # Redundant check: if system is speaking, don't listen at all
    if (state and state.system_speaking) or voice.is_speaking: 
        return ""
    
    try:
        with open('config.json', 'r') as f:
            full_conf = json.load(f)
            conf = full_conf.get('listening', {})
    except:
        return ""

    r = sr.Recognizer()
    r.energy_threshold = conf.get('energy_threshold', 450)
    r.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        # Small delay to avoid hearing the echo of the system's own voice
        if (state and state.system_speaking) or voice.is_speaking: return ""
        
        try:
            is_ptt = state.push_to_talk if state else conf.get('push_to_talk', False)
            
            if not is_ptt or not keyboard:
                # Comportamento continuo classico
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio = r.listen(source, timeout=conf.get('silence_timeout', 5), 
                                 phrase_time_limit=conf.get('phrase_limit', 15))
            else:
                hotkey = state.ptt_hotkey if state else conf.get('ptt_hotkey', 'ctrl+shift')
                # Comportamento Push-To-Talk
                # Attende pressione dell'hotkey (es. 'ctrl+shift')
                while not keyboard.is_pressed(hotkey):
                    try:
                        # Leggiamo per svuotare il buffer di OS e prevenire IOErrors 
                        source.stream.read(source.CHUNK)
                    except Exception:
                        pass
                    if (state and state.system_speaking) or voice.is_speaking: return ""
                    if state and not state.listening_status: return ""
                
                # Hotkey appena premuta
                logger.info("VOICE", f"[PTT] Registrazione in corso... Tieni premuto '{hotkey}'")
                
                # Raccogli raw data dallo stream di PyAudio mentre l'hotkey è tenuta premuta
                audio_data = bytearray()
                # Un timeout di sicurezza interno se teniamo premuto troppo senza parlare
                while keyboard.is_pressed(hotkey):
                    try:
                        buffer = source.stream.read(source.CHUNK)
                        audio_data.extend(buffer)
                    except Exception:
                        pass
                
                if len(audio_data) < 4000: # Troppo corto per essere una frase
                    logger.info("VOICE", "[PTT] Trascrizione annullata: audio troppo corto.")
                    return ""
                    
                logger.info("VOICE", "[PTT] Trascrizione audio con Whisper in corso...")    
                audio = sr.AudioData(bytes(audio_data), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
            
            # If system started speaking WHILE listening, discard everything
            if (state and state.system_speaking) or voice.is_speaking: return ""
            
            text = r.recognize_google(audio, language="it-IT", show_all=False)
            return text.lower()
        except:
            return ""