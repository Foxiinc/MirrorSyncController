@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Portable Build
echo ========================================
echo.

REM Build Backend
echo [1/3] Building Backend...
cd src\MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true -o ..\..\gui\backend_bin
if %ERRORLEVEL% neq 0 (
    echo ERROR: Backend build failed!
    cd ..\..
    exit /b 1
)
cd ..\..
echo [OK] Backend built

REM Generate Python protobuf files
echo [2/3] Generating protobuf files...
cd gui
python generate_proto.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Proto generation failed!
    cd ..
    exit /b 1
)
echo [OK] Protobuf files generated

REM Build GUI with PyInstaller
echo [3/3] Building portable executable...
pyinstaller --onedir --windowed --name MirrorSyncController ^
    --add-data "backend_bin;backend_bin" ^
    --hidden-import=grpc ^
    --hidden-import=google.protobuf ^
    --hidden-import=device_control_pb2 ^
    --hidden-import=device_control_pb2_grpc ^
    launcher.py

if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller build failed!
    cd ..
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Portable executable location:
echo   gui\dist\MirrorSyncController\MirrorSyncController.exe
echo.
echo To run:
echo   gui\dist\MirrorSyncController\MirrorSyncController.exe
echo.
pause