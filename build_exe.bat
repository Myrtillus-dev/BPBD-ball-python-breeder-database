@echo off
echo ============================================
echo  Ball Python Breeder Database - EXE Builder
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Download from https://python.org
    pause & exit /b 1
)

echo Installing PyInstaller...
python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Try running as Administrator.
    pause & exit /b 1
)

echo Building EXE...
python -m PyInstaller --onefile --windowed --name "BallPythonDB" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import sqlite3 ^
    main.py

if errorlevel 1 (
    echo BUILD FAILED. See errors above.
    pause & exit /b 1
)

echo.
echo ============================================
echo  SUCCESS! EXE is in: dist\BallPythonDB.exe
echo ============================================
pause
