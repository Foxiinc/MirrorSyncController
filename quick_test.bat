@echo off
echo ================================================================
echo           MirrorSyncController - Quick Test
echo ================================================================
echo.

echo Checking Backend...
tasklist /FI "IMAGENAME eq MirrorSync.Backend.exe" 2>NUL | find /I /N "MirrorSync.Backend.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Backend is running
) else (
    echo [ERROR] Backend is not running
    echo         Start: src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\MirrorSync.Backend.exe
)

echo.
echo Checking ADB devices...
adb devices | find "device" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Device connected
) else (
    echo [ERROR] Device not connected
)

echo.
echo Checking port forwarding...
adb forward --list | find "4444" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port forwarding configured
) else (
    echo [ERROR] Port forwarding not configured
    echo         Run: adb forward tcp:4444 tcp:4444
)

echo.
echo Checking app on device...
adb shell pm list packages | find "com.mirrorsync.agent" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] App installed
) else (
    echo [ERROR] App not installed
    echo         Install: adb install -r android\app\build\outputs\apk\release\app-release.apk
)

echo.
echo Checking Accessibility Service...
adb shell settings get secure enabled_accessibility_services | find "mirrorsync" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Accessibility Service enabled
) else (
    echo [WARN] Accessibility Service not enabled
    echo         Enable manually in device settings
)

echo.
echo Checking TCP server on device...
adb shell netstat -an | find "4444" >nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] TCP server listening on port 4444
) else (
    echo [WARN] TCP server not found
    echo         Make sure Accessibility Service is enabled
)

echo.
echo ================================================================
echo.
echo View Android logs:
echo    adb logcat -s InAppLogger:* -v time
echo.
echo Test TAP command:
echo    In GUI: Tap X=50, Y=50 -^> Tap
echo.
pause
