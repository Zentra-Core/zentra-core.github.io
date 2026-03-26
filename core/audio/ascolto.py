import speech_recognition as sr
from . import voce
import json
import time

def ascolta(state=None):
    # Redundant check: if system is speaking, don't listen at all
    if (state and state.system_speaking) or voce.is_speaking: 
        return ""
    
    try:
        with open('config.json', 'r') as f:
            conf = json.load(f)['listening']
    except:
        return ""

    r = sr.Recognizer()
    r.energy_threshold = conf.get('energy_threshold', 450)
    r.dynamic_energy_threshold = False
    
    with sr.Microphone() as source:
        # Small delay to avoid hearing the echo of the system's own voice
        if (state and state.system_speaking) or voce.is_speaking: return ""
        
        try:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.2)
            
            audio = r.listen(source, timeout=conf.get('silence_timeout', 5), 
                             phrase_time_limit=conf.get('phrase_limit', 15))
            
            # If system started speaking WHILE listening, discard everything
            if (state and state.system_speaking) or voce.is_speaking: return ""
            
            text = r.recognize_google(audio, language="it-IT", show_all=False)
            return text.lower()
        except:
            return ""