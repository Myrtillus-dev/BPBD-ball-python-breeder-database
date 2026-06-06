@echo off
REM Try python first, then py launcher (Microsoft Store Python)
python --version >nul 2>&1
if errorlevel 1 (
    py main.py
) else (
    python main.py
)
if errorlevel 1 (
    echo.
    echo ERROR: Could not start the application.
    echo Make sure Python is installed: https://python.org
    pause
)
