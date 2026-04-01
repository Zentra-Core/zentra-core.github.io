@echo off
title ZENTRA — Native Web Server (Watchdog)
color 0A

echo.
set /p ZENTRA_VERSION=<core\version
echo  ======================================
echo   ZENTRA NATIVE WEB INTERFACE v%ZENTRA_VERSION%
echo  ======================================
echo.

:: Attiva ambiente virtuale se esiste
if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo [!] Avvio monitor di controllo in modalità WEB...
echo [!] Apertura automatica del browser in corso...
echo.

:: Avviamo il monitor passando il modulo del server web standalone.
python monitor.py --script plugins.web_ui.server

echo.
echo [!] Watchdog terminato.
timeout /t 5
