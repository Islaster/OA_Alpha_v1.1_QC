@echo off
REM ========================================
REM Bounding Box Optimizer - Windows Runner
REM ========================================

setlocal EnableDelayedExpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "BLENDER_PATH_FILE=%SCRIPT_DIR%\blender_path.txt"

REM Check if input provided
if "%~1"=="" (
    echo Usage: %~nx0 input_file.obj [options]
    echo.
    echo Options:
    echo   -o, --output FILE    Output file path
    echo   -c, --config FILE    Configuration file
    echo   --no-ground          Skip ground detection
    echo   --no-learning        Disable learning system
    echo   --type TYPE          Object type/category
    echo   --report FILE        Save report to JSON
    echo   --debug              Enable debug mode
    echo.
    echo Run setup.bat first to configure Blender path!
    pause
    exit /b 1
)

REM Try to get Blender path
set "BLENDER="

REM First check saved path
if exist "%BLENDER_PATH_FILE%" (
    set /p BLENDER=<"%BLENDER_PATH_FILE%"
    if exist "!BLENDER!" (
        goto :found_blender
    )
)

REM Auto-detect if no saved path
for %%V in (4.5 4.4 4.3 4.2 4.1 4.0 3.6 3.5 3.4) do (
    if exist "C:\Program Files\Blender Foundation\Blender %%V\blender.exe" (
        set "BLENDER=C:\Program Files\Blender Foundation\Blender %%V\blender.exe"
        goto :found_blender
    )
)

REM Check PATH
where blender >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('where blender') do (
        set "BLENDER=%%i"
        goto :found_blender
    )
)

echo ERROR: Blender not found!
echo Please run setup.bat first to configure Blender path.
pause
exit /b 1

:found_blender
echo Using Blender: %BLENDER%
echo.

REM Run the optimizer
"%BLENDER%" --background --python "%SCRIPT_DIR%\bounding_box_minimizer.py" -- %*

echo.
echo Done!
