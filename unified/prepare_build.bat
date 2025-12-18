@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Build Preparation
echo ========================================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)
echo [OK] Python found

REM Check .NET
echo Checking .NET...
dotnet --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: .NET not found. Please install .NET 8 SDK
    exit /b 1
)
echo [OK] .NET found

REM Check ADB
echo Checking ADB...
adb version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] ADB not found. Some features will be unavailable
) else (
    echo [OK] ADB found
)

REM Check scrcpy
echo Checking scrcpy...
scrcpy --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] scrcpy not found. Screen mirroring will be unavailable
) else (
    echo [OK] scrcpy found
)

REM Build Backend if needed
if not exist "backend\MirrorSync.Backend.exe" (
    echo.
    echo Building Backend...
    cd ..\src\MirrorSync.Backend
    dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true -o ..\..\unified\backend
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Backend build failed
        cd ..\..
        exit /b 1
    )
    cd ..\..
    echo [OK] Backend built
)

echo.
echo ========================================
echo Preparation completed!
echo ========================================
echo.
echo Next step: run build_unified.bat
echo.
pause