# Installation Guide

Follow these steps to set up Zentra Core on your machine from scratch.

## Prerequisites

1. **Python**: Version 3.10 or higher.
2. **Backends**: Ollama or KoboldCpp (optional but recommended for local LLM).

## Steps

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/). Ensure you check **"Add Python to PATH"** during installation.

### 2. Install AI Backends (Optional)
- **Ollama**: Download from [ollama.com](https://ollama.com/download). Pull a model: `ollama pull gemma2:2b`.
- **KoboldCpp**: Download from [GitHub](https://github.com/LostRuins/koboldcpp/releases) for GGUF/uncensored models.

### 3. Download the Project
Extract the Zentra Core project files into a folder (e.g., `C:\ZentraCore`).

### 4. Install Dependencies
Open a terminal in the project directory and run:
`pip install -r requirements.txt`

### 5. Configure Piper (TTS)
Ensure the `piper/` folder contains the necessary `.onnx` and `.json` files for your preferred language.

### 6. First Launch
Execute the following in the terminal:
`python main.py`

## Common Troubleshooting
- **Hardware telemetry error**: Run `pip install gputil`.
- **Module not found**: Ensure all dependencies are installed via `pip`.
- **Backend not ready**: Start Ollama or KoboldCPP before launching Zentra.
