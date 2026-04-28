import os
import sys
import subprocess
import time

from zentra.tray.config import _ROOT
from zentra.tray.utils import is_zentra_online

# Hold a reference to the subprocess so we can terminate it later
_zentra_process = None

def get_platform_python():
    """Returns the correct python executable depending on the environment."""
    # If running from a venv, sys.executable points to the venv python
    return sys.executable

def start_zentra():
    """
    Spawns the Zentra Core system as a background subprocess of the Tray App.
    """
    global _zentra_process
    if is_zentra_running():
        return  # Already running

    server_script = os.path.join(_ROOT, "zentra", "modules", "web_ui", "server.py")
    if not os.path.exists(server_script):
        print(f"[ORCHESTRATOR] Error: Could not find {server_script}")
        return

    python_exe = get_platform_python()
    
    try:
        if sys.platform == "win32":
            # creationflags=0x08000000 means CREATE_NO_WINDOW (runs silently in background)
            _zentra_process = subprocess.Popen(
                [python_exe, "-m", "zentra.modules.web_ui.server", "--no-gui"],
                cwd=_ROOT,
                creationflags=0x08000000
            )
        else:
            # On Linux/Mac, just run it cleanly in the background
            _zentra_process = subprocess.Popen(
                [python_exe, "-m", "zentra.modules.web_ui.server", "--no-gui"],
                cwd=_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        print("[ORCHESTRATOR] Zentra Core background process spawned successfully.")
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to spawn Zentra Core: {e}")

def stop_zentra():
    """Terminates the background Zentra Core subprocess."""
    global _zentra_process
    if _zentra_process is not None:
        try:
            # Send SIGTERM
            _zentra_process.terminate()
            # Wait up to 3 seconds for graceful shutdown
            _zentra_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            # Force kill if it didn't terminate
            _zentra_process.kill()
        except Exception:
            pass
        _zentra_process = None
        print("[ORCHESTRATOR] Zentra Core process stopped.")
    else:
        # If the Tray was restarted but Zentra was kept alive (detached),
        # we can't kill it by object reference. In extreme cases, one might want
        # to kill by port (7070) here, but for now we rely on proper lifecycle pairing.
        pass

def is_zentra_running() -> bool:
    """
    Returns True if we see the process handle is alive, OR if the port is responding.
    (If the Tray app crashed and was restarted, _zentra_process might be None but is_zentra_online() will be True).
    """
    global _zentra_process
    
    # Fast reliable check if we started it
    if _zentra_process is not None:
        if _zentra_process.poll() is None:
            return True
        else:
            # Process died
            _zentra_process = None
            
    # Fallback: check if the port is bound
    return is_zentra_online()

def restart_zentra():
    """Stops the existing process and spawns a new one."""
    stop_zentra()
    time.sleep(1) # Give port time to release
    start_zentra()
