@echo off
echo Installing MirrorSync Agent APK...

REM Проверяем подключение устройства
adb devices
if %ERRORLEVEL% neq 0 (
    echo ERROR: ADB not found or no devices connected
    pause
    exit /b 1
)

REM Устанавливаем APK
echo Installing APK...
adb install -r app\build\outputs\apk\release\app-release.apk
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install APK
    pause
    exit /b 1
)

echo APK installed successfully!

REM Запускаем приложение
echo Starting MirrorSync Agent...
adb shell am start -n com.mirrorsync.agent/.MainActivity

echo.
echo ========================================
echo NEXT STEPS:
echo 1. Enable Accessibility Service in Android Settings
echo 2. For Android 13+: Allow restricted settings first
echo 3. Check app status in MirrorSync Agent
echo ========================================
echo.

REM Показываем логи
echo Starting logcat (Ctrl+C to stop)...
adb logcat | findstr MirrorAccessibilityService

pause