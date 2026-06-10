@echo off
echo ============================================================
echo  Ball Python Breeder Database - Installer Builder
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. https://python.org
    pause & exit /b 1
)
echo [1/5] Python OK.

echo [2/5] Installing dependencies...
python -m pip install customtkinter pyinstaller --quiet
if errorlevel 1 ( echo ERROR: pip failed. & pause & exit /b 1 )

echo [3/5] Building BallPythonDB.exe...
python -m PyInstaller --onefile --windowed --name "BallPythonDB" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import sqlite3 ^
    --hidden-import customtkinter ^
    --collect-all customtkinter ^
    --icon=icon.ico ^
    main.py
if errorlevel 1 ( echo ERROR: EXE build failed. & pause & exit /b 1 )

REM Code signing (optional - configure PFX_FILE and PFX_PASS to enable)
REM set PFX_FILE=C:\cert\myrtillus.pfx
REM set PFX_PASS=yourpassword
REM signtool sign /f "%PFX_FILE%" /p "%PFX_PASS%" /tr http://timestamp.sectigo.com /td sha256 /fd sha256 "dist\BallPythonDB.exe"
echo [4/5] Code signing skipped (no certificate configured).

echo [5/5] Building installer...
set NSIS=""
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set NSIS="C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe"       set NSIS="C:\Program Files\NSIS\makensis.exe"

if %NSIS%=="" (
    echo ERROR: NSIS not found. Download from https://nsis.sourceforge.io/Download
    echo EXE is ready at: dist\BallPythonDB.exe
    pause & exit /b 1
)

%NSIS% installer.nsi
if errorlevel 1 ( echo ERROR: Installer build failed. & pause & exit /b 1 )

echo.
echo ============================================================
echo  DONE!  Setup_BallPythonDB.exe is ready.
echo ============================================================
pause
