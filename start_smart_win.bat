@echo off
setlocal
set "BASE_DIR=%~dp0"
set "BASE_DIR=%BASE_DIR:~0,-1%"
set "DATA_DIR=%BASE_DIR%\Mixxx_Data"
set "SCRIPT_DIR=%BASE_DIR%\Scripts"
set "PORTABLE_PYTHON=%SCRIPT_DIR%\python_win\python.exe"

:: 1. Prepare Environment (LOAD mode)
"%PORTABLE_PYTHON%" "%SCRIPT_DIR%\mixxx_path_fixer.py" "%DATA_DIR%" "windows" "load"

:: 2. Launch Mixxx
set "MIXXX_EXE=C:\Program Files\Mixxx\mixxx.exe"

if not exist "%MIXXX_EXE%" (
    set "MIXXX_EXE=C:\Program Files (x86)\Mixxx\mixxx.exe"
)
if not exist "%MIXXX_EXE%" (
    set "MIXXX_EXE=%LOCALAPPDATA%\Mixxx\mixxx.exe"
)
if not exist "%MIXXX_EXE%" (
    echo Error: Could not find mixxx.exe in standard directories.
    pause
    exit /b
)

start /wait "" "%MIXXX_EXE%" --settingsPath "%DATA_DIR%"

:: 3. Post-Flight (SAVE mode)
echo Mixxx closed. Saving machine-specific hardware settings...
"%PORTABLE_PYTHON%" "%SCRIPT_DIR%\mixxx_path_fixer.py" "%DATA_DIR%" "windows" "save"
echo Done.