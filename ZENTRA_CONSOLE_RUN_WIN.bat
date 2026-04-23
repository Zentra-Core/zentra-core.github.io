@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title ZENTRA CORE - ACTIVE SESSION RUNNER (Native Text Console)
cd /d "%~dp0"

echo.
set ZENTRA_VERSION=Unknown
if exist zentra\core\version set /p ZENTRA_VERSION=<zentra\core\version
echo  ==============================================================
echo   ZENTRA CORE NATIVE TERMINAL v%ZENTRA_VERSION%
echo  ==============================================================
echo.

:: Priority to the isolated portable python runtime
set PYTHON_CMD=python
if exist "%CD%\python_env\python.exe" (
  set PYTHON_CMD="%CD%\python_env\python.exe"
) else if exist "venv\Scripts\python.exe" (
  set PYTHON_CMD="%CD%\venv\Scripts\python.exe"
) else if exist "venv\Scripts\activate.bat" (
  call venv\Scripts\activate.bat
)

echo [*] Starting interactive terminal...
echo [*] Press F9 for a Safe Restart of the program.
echo.

!PYTHON_CMD! zentra\monitor.py

echo.
echo [!] Process terminated.
pause