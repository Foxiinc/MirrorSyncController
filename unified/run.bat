@echo off
setlocal enabledelayedexpansion

REM Check if executable exists
if not exist "dist\MirrorSyncController\MirrorSyncController.exe" (
    echo ERROR: Executable not found
    echo Please run build_all.bat first
    pause
    exit /b 1
)

REM Run the application
echo Starting MirrorSync Controller...
start "" "dist\MirrorSyncController\MirrorSyncController.exe"