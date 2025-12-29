@echo off
REM ========================================
REM Setup script for Bounding Box Optimizer - Windows
REM Auto-detects Blender or prompts for path
REM ========================================

setlocal EnableDelayedExpansion

echo ========================================
echo Bounding Box Optimizer - Windows Setup
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "BLENDER_PATH_FILE=%SCRIPT_DIR%\blender_path.txt"

REM Check if we have a saved Blender path
if exist "%BLENDER_PATH_FILE%" (
    set /p BLENDER=<"%BLENDER_PATH_FILE%"
    if exist "!BLENDER!" (
        echo Using saved Blender path: !BLENDER!
        goto :found_blender
    ) else (
        echo Saved Blender path no longer valid, searching...
        del "%BLENDER_PATH_FILE%" 2>nul
    )
)

REM Try to find Blender automatically
set "BLENDER="
echo Searching for Blender installation...
echo.

REM Check all common Windows installation paths (newest to oldest)
REM Blender 4.x versions
for %%V in (4.5 4.4 4.3 4.2 4.1 4.0) do (
    if exist "C:\Program Files\Blender Foundation\Blender %%V\blender.exe" (
        set "BLENDER=C:\Program Files\Blender Foundation\Blender %%V\blender.exe"
        goto :found_blender
    )
)

REM Blender 3.x versions
for %%V in (3.6 3.5 3.4 3.3 3.2 3.1 3.0) do (
    if exist "C:\Program Files\Blender Foundation\Blender %%V\blender.exe" (
        set "BLENDER=C:\Program Files\Blender Foundation\Blender %%V\blender.exe"
        goto :found_blender
    )
)

REM Check generic paths
if exist "C:\Program Files\Blender Foundation\Blender\blender.exe" (
    set "BLENDER=C:\Program Files\Blender Foundation\Blender\blender.exe"
    goto :found_blender
)

REM Check Program Files (x86) just in case
if exist "C:\Program Files (x86)\Blender Foundation\Blender\blender.exe" (
    set "BLENDER=C:\Program Files (x86)\Blender Foundation\Blender\blender.exe"
    goto :found_blender
)

REM Check user's home directory (portable installs)
if exist "%USERPROFILE%\Blender\blender.exe" (
    set "BLENDER=%USERPROFILE%\Blender\blender.exe"
    goto :found_blender
)

REM Check Steam installation
if exist "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe" (
    set "BLENDER=C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
    goto :found_blender
)

REM Check if blender is in PATH
where blender >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('where blender') do (
        set "BLENDER=%%i"
        goto :found_blender
    )
)

REM Not found - ask user for path
echo.
echo ========================================
echo Blender not found automatically!
echo ========================================
echo.
echo Common installation locations:
echo   - C:\Program Files\Blender Foundation\Blender 4.2\blender.exe
echo   - C:\Program Files\Blender Foundation\Blender\blender.exe
echo.
echo Please enter the full path to blender.exe
echo (You can copy-paste from File Explorer)
echo.
set /p BLENDER="Blender path: "

REM Remove quotes if user included them
set "BLENDER=!BLENDER:"=!"

REM Validate the path
if not exist "!BLENDER!" (
    echo.
    echo ERROR: File not found: !BLENDER!
    echo Please check the path and try again.
    pause
    exit /b 1
)

REM Save the path for future use
echo !BLENDER!>"%BLENDER_PATH_FILE%"
echo.
echo Path saved for future use.

:found_blender
echo.
echo Found Blender: %BLENDER%
echo.

REM Save path if not already saved
if not exist "%BLENDER_PATH_FILE%" (
    echo %BLENDER%>"%BLENDER_PATH_FILE%"
)

REM Create Python script to install dependencies
echo Creating install script...
(
echo import subprocess
echo import sys
echo.
echo print^("Installing dependencies into Blender's Python..."^)
echo print^(f"Python executable: {sys.executable}"^)
echo print^(f"Python version: {sys.version}"^)
echo print^(""^)
echo.
echo packages = ["scipy", "numpy"]
echo.
echo for package in packages:
echo     print^(f"Installing {package}..."^)
echo     try:
echo         subprocess.check_call^([sys.executable, "-m", "pip", "install", "--upgrade", package]^)
echo         print^(f"  Done!"^)
echo     except Exception as e:
echo         print^(f"  Warning: {e}"^)
echo.
echo print^(""^)
echo print^("Setup complete!"^)
) > "%SCRIPT_DIR%\_install_deps.py"

REM Run the install script through Blender
echo.
echo Installing dependencies into Blender's Python...
echo.
"%BLENDER%" --background --python "%SCRIPT_DIR%\_install_deps.py"

REM Clean up
del "%SCRIPT_DIR%\_install_deps.py" 2>nul

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Blender path saved to: %BLENDER_PATH_FILE%
echo.
echo You can now run:
echo   - run_optimizer.bat input_file.obj  (command line)
echo   - run_gui.bat                       (GUI mode)
echo.
pause
