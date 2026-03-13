@echo off
setlocal
set "BASE_DIR=%~dp0"
set "BASE_DIR=%BASE_DIR:~0,-1%"
set "DATA_DIR=%BASE_DIR%\Mixxx_Data"
set "SCRIPT_DIR=%BASE_DIR%\Scripts"
set "PORTABLE_PYTHON=%SCRIPT_DIR%\python_win\python.exe"

echo ==========================================
echo     MIXXX SMART LAUNCHER (WINDOWS)
echo ==========================================

:: 1. Check for Portable Python
if not exist "%PORTABLE_PYTHON%" (
    echo ❌ ERROR: Portable Python not found in %PORTABLE_PYTHON%
    echo Please ensure the 'python_win' folder exists in your Scripts directory.
    pause
    exit /b
)

:: 2. Prepare Environment
"%PORTABLE_PYTHON%" "%SCRIPT_DIR%\mixxx_path_fixer.py" "%DATA_DIR%" "windows" "load"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Initialization failed.
    pause
    exit /b
)

:: 3. Find Mixxx
set "MIXXX_EXE=C:\Program Files\Mixxx\mixxx.exe"
if not exist "%MIXXX_EXE%" set "MIXXX_EXE=C:\Program Files (x86)\Mixxx\mixxx.exe"
if not exist "%MIXXX_EXE%" set "MIXXX_EXE=%LOCALAPPDATA%\Mixxx\mixxx.exe"

if not exist "%MIXXX_EXE%" (
    echo ❌ ERROR: Mixxx is not installed on this PC.
    echo Please download it from: https://mixxx.org/download/
    pause
    exit /b
)

:: 4. Launch
start /wait "" "%MIXXX_EXE%" --settingsPath "%DATA_DIR%"

:: 5. Save
echo Saving machine settings...
"%PORTABLE_PYTHON%" "%SCRIPT_DIR%\mixxx_path_fixer.py" "%DATA_DIR%" "windows" "save"
echo Done.