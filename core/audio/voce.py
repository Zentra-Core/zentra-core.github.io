import subprocess
import os
import winsound
import json
import time
import keyboard 
import msvcrt
is_speaking = False

def parla(text, state=None):
    global is_speaking
    if not text: return
    
    # 1. Loading full configuration
    try:
        with open('config.json', 'r') as f:
            full_conf = json.load(f)
            c = full_conf.get('voice', {})
            
            # Piper parameters mapping
            # Invert speed: UI 2.0 (fast) -> Piper 0.5 (half duration)
            length_scale = 1.0 / max(0.1, c.get('speed', 1.0))
            # Noise Scale (0.0 - 1.0): Controls pitch variability
            noise_scale = c.get('noise_scale', 0.667)
            # Noise W (0.0 - 1.0): Controls phoneme stability
            noise_w = c.get('noise_w', 0.8)
            # Sentence Silence: Seconds of pause between periods
            sentence_silence = c.get('sentence_silence', 0.2)
            
    except Exception as e:
        print(f"[VOICE] Configuration error: {e}")
        length_scale, noise_scale, noise_w, sentence_silence = 1.0, 0.667, 0.8, 0.2

    is_speaking = True
    if state:
        state.system_speaking = True
    
    try:
        # Reload or use previous config
        with open('config.json', 'r') as f:
             c_voice = json.load(f).get('voice', {})
    except Exception:
        c_voice = {}
        
    try:
        clean_text = text.replace('"', '').replace('\n', ' ')
        piper_path = c_voice.get('piper_path', r"C:\piper\piper.exe")
        model_path = c_voice.get('onnx_model', r"C:\piper\en_US-lessac-medium.onnx")
        
        # 2. Complete command with all possible flags
        command = [
            piper_path, "-m", model_path,
            "--length_scale", str(length_scale),
            "--noise_scale", str(noise_scale),
            "--noise_w", str(noise_w),
            "--sentence_silence", str(sentence_silence),
            "-f", "risposta.wav"
        ]
        
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        proc.communicate(input=clean_text)
        
        if os.path.exists("risposta.wav"):
            winsound.PlaySound("risposta.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            
            # Dynamic duration calculation based on real speed (conservative: 12 char/sec)
            estimated_duration = (len(clean_text) / 12) * length_scale + sentence_silence
            start_time = time.time()

            while (time.time() - start_time) < estimated_duration:
                if keyboard.is_pressed('esc'):
                    # Flush msvcrt buffer to avoid double ESC activations
                    while msvcrt.kbhit():
                        msvcrt.getch()
                    if state:
                        state.last_voice_stop = time.time()
                    stop_voice()
                    break
                time.sleep(0.05)
                
    except Exception as e:
        print(f"[VOICE] Piper execution error: {e}")
    finally:
        # Extra generous buffer for ambient silence and reverb
        time.sleep(1.2)
        is_speaking = False
        if state:
            state.system_speaking = False

def stop_voice():
    global is_speaking
    winsound.PlaySound(None, winsound.SND_PURGE)
    is_speaking = False