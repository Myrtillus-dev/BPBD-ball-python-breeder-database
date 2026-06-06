@echo off
echo ============================================================
echo  Ball Python Breeder Database - Installer Builder
echo ============================================================
echo.

REM ── Vaihe 1: Python ──────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. https://python.org
    pause & exit /b 1
)
echo [1/5] Python OK.

REM ── Vaihe 2: PyInstaller ─────────────────────────────────────
echo [2/5] Installing PyInstaller...
python -m pip install pyinstaller --quiet
if errorlevel 1 ( echo ERROR: pip failed. & pause & exit /b 1 )

REM ── Vaihe 3: Build EXE ───────────────────────────────────────
echo [3/5] Building BallPythonDB.exe...
python -m PyInstaller --onefile --windowed --name "BallPythonDB" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import sqlite3 ^
    --icon=icon.ico ^
    main.py
if errorlevel 1 ( echo ERROR: EXE build failed. & pause & exit /b 1 )

REM ── Vaihe 4: Digitaalinen allekirjoitus (valinnainen) ─────────
REM Jos sinulla on .pfx sertifikaatti, aseta polku alle ja poista REM
REM set PFX_FILE=C:\cert\myrtillus.pfx
REM set PFX_PASS=salasanasi
REM signtool sign /f "%PFX_FILE%" /p "%PFX_PASS%" /tr http://timestamp.sectigo.com /td sha256 /fd sha256 "dist\BallPythonDB.exe"
REM if errorlevel 1 ( echo WARNING: Signing failed, continuing without signature. )
echo [4/5] Code signing skipped (no certificate configured).
echo       To sign: edit build_installer.bat and set PFX_FILE + PFX_PASS

REM ── Vaihe 5: NSIS Installer ──────────────────────────────────
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
echo  Share this one file with your users.
echo ============================================================
pause
