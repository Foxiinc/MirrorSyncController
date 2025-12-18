@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Complete Build
echo ========================================
echo.

REM Step 1: Prepare
echo [1/3] Preparing build environment...
call prepare_build.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Preparation failed
    exit /b 1
)

REM Step 2: Build unified
echo.
echo [2/3] Building unified executable...
call build_unified.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed
    exit /b 1
)

REM Step 3: Verify
echo.
echo [3/3] Verifying build...
if exist "dist\MirrorSyncController\MirrorSyncController.exe" (
    echo [OK] Executable created successfully
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable: dist\MirrorSyncController\MirrorSyncController.exe
    echo.
    echo To run:
    echo   dist\MirrorSyncController\MirrorSyncController.exe
    echo.
) else (
    echo ERROR: Executable not found
    exit /b 1
)

pause