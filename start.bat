@echo off
title KavachGrid 3.0 Launcher
cd /d "%~dp0"

if exist "KavachGrid.exe" (
    echo Starting KavachGrid via KavachGrid.exe...
    "KavachGrid.exe" %*
) else (
    echo Starting KavachGrid via Python launcher...
    python launcher.py %*
)
if %errorlevel% neq 0 (
    echo.
    echo System exited with code %errorlevel%
    pause
)
