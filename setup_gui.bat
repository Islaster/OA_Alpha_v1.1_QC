@echo off
REM ========================================
REM Setup script for OA GUI - Windows
REM Creates a virtual environment and installs PySide6
REM ========================================

echo ========================================
echo OA - Orientation Automator GUI Setup
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "VENV_DIR=%SCRIPT_DIR%\venv"

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or later from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Using Python:
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo Done!
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install PySide6
echo.
echo Installing PySide6...
pip install PySide6

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Setup complete!
    echo ========================================
    echo.
    echo To run the GUI:
    echo   run_gui.bat
    echo.
) else (
    echo.
    echo ERROR: Failed to install PySide6
    pause
    exit /b 1
)

pause

