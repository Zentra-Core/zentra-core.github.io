@echo off
echo ==================================================
echo   ZENTRA CORE - ENABLE TRAY AUTOSTART
echo ==================================================
echo.

:: Determine paths
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\..\..\.."
set ZENTRA_ROOT=%CD%

set TRAY_RUNNER=%ZENTRA_ROOT%\scripts\windows\run\ZENTRA_TRAY_WIN.bat

if not exist "%TRAY_RUNNER%" (
    echo [!] ERROR: Could not find ZENTRA_TRAY_WIN.bat at:
    echo     %TRAY_RUNNER%
    pause
    exit /b 1
)

echo [*] Adding Zentra Tray to Current User Autostart...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZentraCoreTray" /t REG_SZ /d "\"%TRAY_RUNNER%\"" /f

echo.
echo [+] Done! The Zentra Tray Icon will now launch automatically
echo     every time you log into Windows.
echo.
pause
