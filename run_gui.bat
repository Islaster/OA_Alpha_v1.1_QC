@echo off
REM ========================================
REM Run the OA GUI - Windows
REM ========================================

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Virtual environment not found!
    echo Please run setup_gui.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment and run GUI
call "%VENV_DIR%\Scripts\activate.bat"
python "%SCRIPT_DIR%\gui.py"

