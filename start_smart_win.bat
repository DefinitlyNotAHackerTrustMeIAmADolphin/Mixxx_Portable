@echo off
setlocal
:: Get the drive/folder of the script
set "BASE_DIR=%~dp0"
set "BASE_DIR=%BASE_DIR:~0,-1%"
set "DATA_DIR=%BASE_DIR%\Mixxx_Data"
set "MIXXX_EXE=C:\Program Files\Mixxx\mixxx.exe"

:: Path to our PORTABLE Python
set "PORTABLE_PYTHON=%DATA_DIR%\python_win\python.exe"

echo [WINDOWS MODE] Swapping in Windows settings...

:: 1. Restore Windows-specific Hardware Config
if exist "%DATA_DIR%\mixxx.cfg.win" (
    copy /Y "%DATA_DIR%\mixxx.cfg.win" "%DATA_DIR%\mixxx.cfg" >nul
)

:: 2. Run the Portable Python to fix paths
if exist "%PORTABLE_PYTHON%" (
    "%PORTABLE_PYTHON%" "%DATA_DIR%\mixxx_path_fixer.py" "%DATA_DIR%" "windows"
) else (
    echo Error: Portable Python not found at %PORTABLE_PYTHON%
    pause
    exit /b
)

:: 3. Launch Mixxx
if not exist "%MIXXX_EXE%" (
    echo Error: Mixxx not found at %MIXXX_EXE%
    echo Please ensure Mixxx is installed on this machine.
    pause
    exit /b
)

start /wait "" "%MIXXX_EXE%" --settingsPath "%DATA_DIR%"

:: 4. Save changes back
echo Mixxx closed. Saving Windows settings...
copy /Y "%DATA_DIR%\mixxx.cfg" "%DATA_DIR%\mixxx.cfg.win" >nul
echo Done.