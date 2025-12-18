@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Unified Build
echo ========================================
echo.

REM Check if Backend exists
if not exist "backend\MirrorSync.Backend.exe" (
    echo ERROR: Backend executable not found in backend\ directory
    echo Please copy MirrorSync.Backend.exe to backend\ folder
    exit /b 1
)

echo [1/2] Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo [2/2] Building portable executable...
pyinstaller --onedir --windowed --name MirrorSyncController ^
    --add-data "gui;gui" ^
    --add-data "backend;backend" ^
    --hidden-import=grpc ^
    --hidden-import=google.protobuf ^
    --hidden-import=device_control_pb2 ^
    --hidden-import=device_control_pb2_grpc ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Portable executable: dist\MirrorSyncController\MirrorSyncController.exe
echo.
pause