@echo off
title Zentra — AI Web Interface
color 0A

echo.
echo  ======================================
echo   ZENTRA NATIVE WEB INTERFACE
echo   Avvio del server locale su porta 7070
echo  ======================================
echo.

:: Attiva ambiente virtuale se esiste
if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

:: Avvia il server Flask (config + chat)
start "Zentra Web Server" python -m plugins.web_ui.server

:: Aspetta 2 secondi e poi apri il browser
timeout /t 2 /nobreak >nul
echo  Apertura browser su http://127.0.0.1:7070/chat ...
start http://127.0.0.1:7070/chat

echo.
echo  Server avviato! Puoi chiudere questa finestra.
echo  Il server continua a girare in background.
echo.
pause
