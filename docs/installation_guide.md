# Installation Guide - Zentra Core
(For clean installation from scratch)

---

## 1. Install Python
- Go to [python.org](https://www.python.org/downloads/)
- Download Python 3.10 or higher.
- During installation, check **"Add Python to PATH"**.
- Complete the installation.

## 2. Install Ollama (Optional, for local LLMs)
- Go to [ollama.com](https://ollama.com/download)
- Download and install Ollama.
- Open a terminal and download a model (e.g., `ollama pull gemma2:2b`).

## 3. Install KoboldCpp (Optional, for GGUF/Uncensored models)
- Go to [KoboldCpp Releases](https://github.com/LostRuins/koboldcpp/releases).
- Download the latest `koboldcpp.exe`.
- Place it in a folder (e.g., `C:\KoboldCPP\`).
- Create a `models/` subfolder and download GGUF models there.

## 4. Download Zentra Core
- Clone or extract the Zentra Core project into a folder (e.g., `C:\ZentraCore`).

## 5. Install Python Dependencies
- Open a terminal in the project folder.
- Run: `pip install -r requirements.txt`

## 6. Configure Piper (TTS)
- Ensure the `piper/` folder contains:
    - `piper.exe`
    - `en_US-lessac-medium.onnx` (for English) or your preferred voice.
    - Accompanying `.json` files.
- Verify voice paths in `config.json` under the "voice" section.

## 7. First Run
- Open a terminal in the project folder.
- Run: `python main.py`
- If successful, you will see the Zentra terminal interface.

---

## 8. Common Troubleshooting
- **"Hardware telemetry error"**: Install gputil: `pip install gputil`.
- **"Module not found"**: Ensure all dependencies are installed via `requirements.txt`.
- **"Backend not ready"**: Start Ollama or KoboldCPP before launching Zentra.
