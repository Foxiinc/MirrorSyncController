@echo off
echo ================================================================
echo        MirrorSyncController - System Testing
echo ================================================================
echo.

:: ============================================================================
:: 1. CHECK ADB AND DEVICES
:: ============================================================================
echo [1/5] Checking ADB and devices...
echo.

where adb >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] ADB not found in PATH!
    echo         Add Android SDK platform-tools to PATH
    pause
    exit /b 1
)

echo [OK] ADB found
echo.

echo Connected devices:
adb devices
echo.

echo Checking devices...
set DEVICE_FOUND=
for /f "skip=1 tokens=1,2" %%a in ('adb devices') do (
    if "%%b"=="device" (
        echo [OK] Device found: %%a
        set DEVICE_FOUND=1
        set DEVICE_SERIAL=%%a
    )
)

if not defined DEVICE_FOUND (
    echo [ERROR] No devices connected!
    echo.
    echo Make sure:
    echo    1. Device is connected via USB
    echo    2. USB Debugging is enabled
    echo    3. Debugging permission is granted
    echo.
    pause
    exit /b 1
)

echo.
pause

:: ============================================================================
:: 2. INSTALL APK
:: ============================================================================
echo.
echo [2/5] Installing Android APK...
echo.

set APK_PATH=android\app\build\outputs\apk\release\app-release.apk

if not exist "%APK_PATH%" (
    echo [ERROR] APK not found: %APK_PATH%
    echo         Run BUILD_AND_TEST.bat first
    pause
    exit /b 1
)

echo Installing APK on device...
adb install -r "%APK_PATH%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] APK installation failed
    pause
    exit /b 1
)

echo [OK] APK installed successfully
echo.
pause

:: ============================================================================
:: 3. SETUP PORT FORWARDING
:: ============================================================================
echo.
echo [3/5] Setting up ADB port forwarding...
echo.

echo Removing old rules...
adb forward --remove-all

echo Setting up forwarding for port 4444...
adb forward tcp:4444 tcp:4444
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Port forwarding setup failed
    pause
    exit /b 1
)

echo [OK] Port forwarding configured
echo.

echo Checking forwarding rules:
adb forward --list
echo.
pause

:: ============================================================================
:: 4. START BACKEND
:: ============================================================================
echo.
echo [4/5] Starting Backend...
echo.

set BACKEND_PATH=src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\MirrorSync.Backend.exe

if not exist "%BACKEND_PATH%" (
    echo [ERROR] Backend not found: %BACKEND_PATH%
    echo         Run BUILD_AND_TEST.bat first
    pause
    exit /b 1
)

echo Starting Backend in separate window...
start "MirrorSync Backend" "%BACKEND_PATH%"

echo [OK] Backend started
echo      Check "MirrorSync Backend" window
echo.

timeout /t 5 /nobreak >nul
pause

:: ============================================================================
:: 5. TESTING INSTRUCTIONS
:: ============================================================================
echo.
echo [5/5] Testing instructions...
echo.
echo ================================================================
echo.
echo [SUCCESS] System ready for testing!
echo.
echo ON ANDROID DEVICE:
echo    1. Open "MirrorSync Agent" app
echo    2. Click "Open Accessibility Settings"
echo    3. Find "MirrorSync Agent" and enable it
echo    4. Return to app
echo    5. Check status:
echo       [OK] Accessibility Service: RUNNING
echo       [OK] TCP Server: Listening on port 4444
echo    6. Click "View Logs" to see logs
echo.
echo ON COMPUTER:
echo    1. Open new command prompt
echo    2. cd gui
echo    3. python main_window.py
echo    4. In GUI click "Refresh" to find devices
echo    5. Device should appear in list
echo.
echo TEST COMMANDS:
echo    1. Select device in GUI
echo    2. Set Tap X=50, Y=50 (center)
echo    3. Click "Tap"
echo    4. Tap should happen in center of screen
echo    5. Check logs in app (View Logs)
echo.
echo CHECK LOGS:
echo    - Backend: "MirrorSync Backend" window
echo    - Android: App -^> View Logs
echo    - ADB: adb logcat -s InAppLogger:*
echo.
echo EXPECTED LOGS (Android):
echo    I/MainActivity: MainActivity created
echo    I/MirrorAccessibilityService: Accessibility service connected
echo    I/TcpServerService: TCP server listening on port 4444
echo    I/TcpServerService: Client connected
echo    D/TcpServerService: PING -^> PONG
echo    D/MirrorAccessibilityService: TAP (0.5, 0.5)
echo    I/MirrorAccessibilityService: TAP seq=1 [OK] XXms
echo.
echo ================================================================
echo.
echo Press any key to start GUI...
pause >nul

cd gui
python main_window.py

exit /b 0
