# Installation Guide

Follow these steps to set up Zentra Core on your machine.

## Prerequisites

1. **Python**: Version 3.10 or higher.
2. **Backends**: Ollama or KoboldCpp (optional but recommended).

## Steps

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/). Ensure you check "Add Python to PATH" during installation.

### 2. Install AI Backends (Optional)
- **Ollama**: Download from [ollama.com](https://ollama.com/download). Pull a model: `ollama pull gemma2:2b`.
- **KoboldCpp**: Download from [GitHub](https://github.com/LostRuins/koboldcpp/releases).

### 3. Clone and Setup
Extract the project files or clone the repository.

### 4. Install Dependencies
Open a terminal in the project directory and run:
`pip install -r requirements.txt`

### 5. Configure Piper (TTS)
Ensure the `piper/` folder contains the necessary `.onnx` and `.json` files.

### 6. Run Zentra
Execute the following in the terminal:
`python main.py`
