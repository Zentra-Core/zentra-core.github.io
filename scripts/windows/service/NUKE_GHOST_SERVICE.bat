@echo off
echo ==================================================
echo   ZENTRA CORE - GHOST SERVICE REMOVAL TOOL
echo ==================================================
echo.

:: Check Admin Rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [*] Administrator privileges detected. Proceeding.
) else (
    echo [!] ERROR: This script must be run as Administrator!
    echo     Please right-click and "Run as Administrator".
    pause
    exit /b 1
)

echo [*] Attempting to force-stop ZentraCore...
sc stop ZentraCore >nul 2>&1

echo [*] Forcibly removing ZentraCore from the Registry...
reg delete "HKLM\System\CurrentControlSet\Services\ZentraCore" /f >nul 2>&1

echo [*] Asking Windows to delete the Service...
sc delete ZentraCore >nul 2>&1

echo.
echo [+] Done! The ghost service has been obliterated from Windows.
echo     (If it still shows in Task Manager, simply close and reopen Task Manager)
echo.
pause
