@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Agent Diagnostics
echo ========================================
echo.

echo [1] Checking if app is installed...
adb shell pm list packages | find "mirrorsync" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] App installed
) else (
    echo [ERROR] App not installed
    exit /b 1
)

echo.
echo [2] Checking Accessibility Service...
adb shell settings get secure enabled_accessibility_services | find "mirrorsync" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Accessibility Service enabled
) else (
    echo [WARN] Accessibility Service not enabled
)

echo.
echo [3] Checking if service is running...
adb shell ps | find "mirrorsync" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Process running
) else (
    echo [WARN] Process not running
)

echo.
echo [4] Checking port 4444...
adb shell netstat 2>nul | find "4444" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Port 4444 listening
) else (
    echo [WARN] Port 4444 not listening
)

echo.
echo [5] Clearing and viewing logs...
adb logcat -c
echo Waiting for logs...
timeout /t 2 /nobreak
adb logcat -v time | find "mirrorsync" | find /v "^$"

echo.
echo ========================================
echo Diagnostics complete
echo ========================================