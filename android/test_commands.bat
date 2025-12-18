@echo off
echo Testing MirrorSync Agent commands...

REM Проверяем, что устройство подключено
adb devices | findstr "device$" >nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: No Android device connected
    pause
    exit /b 1
)

REM Проверяем, что Accessibility Service включен
echo Checking if Accessibility Service is enabled...
adb shell settings get secure enabled_accessibility_services | findstr "mirrorsync" >nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: Accessibility Service may not be enabled
    echo Please enable it in Settings -> Accessibility -> MirrorSync Agent
    echo.
)

REM Настраиваем port forwarding
echo Setting up port forwarding...
adb forward tcp:4444 tcp:4444

REM Проверяем, что TCP сервер запущен
echo Checking TCP server...
timeout /t 2 >nul
netstat -an | findstr ":4444" >nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: TCP server may not be running
    echo Make sure MirrorSync Agent is running and Accessibility Service is enabled
    echo.
)

echo.
echo ========================================
echo MANUAL TESTS:
echo 1. Test tap: Send TAP command to center of screen
echo 2. Test swipe: Send SWIPE command
echo 3. Check logs: adb logcat ^| findstr MirrorAccessibilityService
echo ========================================
echo.

REM Показываем текущие логи
echo Recent logs:
adb logcat -d | findstr MirrorAccessibilityService | tail -10

echo.
echo Press any key to start live logcat monitoring...
pause >nul

echo Starting live logcat (Ctrl+C to stop)...
adb logcat | findstr MirrorAccessibilityService