@echo off
@chcp 65001 >nul
title ZENTRA PROCESS MANAGER
pushd "%~dp0"
cd ..\..\..
set ROOT_DIR=%CD%
popd
cd /d "%ROOT_DIR%"
color 0D

echo.
set ZENTRA_VERSION=Unknown
if exist zentra\core\version set /p ZENTRA_VERSION=<zentra\core\version
echo  ==============================================================
echo   ZENTRA PROCESS MANAGER v%ZENTRA_VERSION%
echo  ==============================================================
echo.

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo [*] Starting standalone process monitor...
echo.

python scripts\utils\zentra_proc_manager.py

echo.
echo [!] Process terminated.
pause
