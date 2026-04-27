@echo off
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\..\..\.."

@REM Starts the Zentra Core System Tray Orchestrator quietly
start "" /b pythonw -m zentra.tray.tray_app
