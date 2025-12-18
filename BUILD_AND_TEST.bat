@echo off
echo ================================================================
echo      MirrorSyncController - Full Build and Test
echo ================================================================
echo.

set ERROR_OCCURRED=0

:: ============================================================================
:: 1. CHECK ENVIRONMENT
:: ============================================================================
echo [1/6] Checking environment...
echo.

where dotnet >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] .NET SDK not found!
    echo         Install .NET 8 SDK: https://dotnet.microsoft.com/download
    set ERROR_OCCURRED=1
    goto :error
)
echo [OK] .NET SDK found

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    set ERROR_OCCURRED=1
    goto :error
)
echo [OK] Python found

where adb >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] ADB not found in PATH
    echo        Make sure Android SDK is installed
) else (
    echo [OK] ADB found
)

if exist "android\gradlew.bat" (
    echo [OK] Gradle wrapper found
) else (
    echo [ERROR] Gradle wrapper not found!
    set ERROR_OCCURRED=1
    goto :error
)

echo.
pause

:: ============================================================================
:: 2. CLEAN PREVIOUS BUILDS
:: ============================================================================
echo.
echo [2/6] Cleaning previous builds...
echo.

if exist "src\MirrorSync.Backend\bin" rmdir /s /q "src\MirrorSync.Backend\bin"
if exist "src\MirrorSync.Backend\obj" rmdir /s /q "src\MirrorSync.Backend\obj"
if exist "src\MirrorSync.Protos\bin" rmdir /s /q "src\MirrorSync.Protos\bin"
if exist "src\MirrorSync.Protos\obj" rmdir /s /q "src\MirrorSync.Protos\obj"
if exist "android\app\build" rmdir /s /q "android\app\build"
if exist "gui\dist" rmdir /s /q "gui\dist"
if exist "gui\build" rmdir /s /q "gui\build"

echo [OK] Clean completed
echo.
pause

:: ============================================================================
:: 3. BUILD BACKEND (.NET 8)
:: ============================================================================
echo.
echo [3/6] Building Backend (.NET 8)...
echo.

cd src\MirrorSync.Backend

echo Restoring dependencies...
dotnet restore
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend restore failed
    set ERROR_OCCURRED=1
    cd ..\..
    goto :error
)

echo Building Release...
dotnet build -c Release
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend build failed
    set ERROR_OCCURRED=1
    cd ..\..
    goto :error
)

echo Publishing...
dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=false
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend publish failed
    set ERROR_OCCURRED=1
    cd ..\..
    goto :error
)

cd ..\..
echo [OK] Backend built successfully
echo      Path: src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish
echo.
pause

:: ============================================================================
:: 4. BUILD ANDROID APK
:: ============================================================================
echo.
echo [4/6] Building Android APK...
echo.

cd android

echo Cleaning Gradle cache...
call gradlew.bat clean
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Gradle clean failed
)

echo Building Release APK...
call gradlew.bat assembleRelease
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Android APK build failed
    set ERROR_OCCURRED=1
    cd ..
    goto :error
)

cd ..
echo [OK] Android APK built successfully
echo      Path: android\app\build\outputs\apk\release\app-release.apk
echo.
pause

:: ============================================================================
:: 5. INSTALL PYTHON DEPENDENCIES
:: ============================================================================
echo.
echo [5/6] Installing Python dependencies...
echo.

cd gui

if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo [WARN] Python dependencies install failed
    ) else (
        echo [OK] Python dependencies installed
    )
) else (
    echo [WARN] requirements.txt not found
)

cd ..
echo.
pause

:: ============================================================================
:: 6. TESTING
:: ============================================================================
echo.
echo [6/6] Testing components...
echo.

echo Checking Backend...
if exist "src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\MirrorSync.Backend.exe" (
    echo [OK] Backend executable found
) else (
    echo [ERROR] Backend executable not found!
    set ERROR_OCCURRED=1
)

echo Checking Android APK...
if exist "android\app\build\outputs\apk\release\app-release.apk" (
    echo [OK] Android APK found
) else (
    echo [ERROR] Android APK not found!
    set ERROR_OCCURRED=1
)

echo Checking GUI...
if exist "gui\main_window.py" (
    echo [OK] GUI files found
) else (
    echo [ERROR] GUI files not found!
    set ERROR_OCCURRED=1
)

echo.
echo ================================================================
echo.

if %ERROR_OCCURRED% EQU 0 (
    echo [SUCCESS] ALL COMPONENTS BUILT SUCCESSFULLY!
    echo.
    echo Next steps:
    echo.
    echo 1. Start Backend:
    echo    cd src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish
    echo    MirrorSync.Backend.exe
    echo.
    echo 2. Install Android APK:
    echo    adb install -r android\app\build\outputs\apk\release\app-release.apk
    echo.
    echo 3. Setup device:
    echo    - Enable Accessibility Service
    echo    - Setup ADB port forwarding: adb forward tcp:4444 tcp:4444
    echo.
    echo 4. Start GUI:
    echo    cd gui
    echo    python main_window.py
    echo.
    goto :success
) else (
    goto :error
)

:error
echo.
echo ================================================================
echo [ERROR] BUILD FAILED!
echo.
echo Check:
echo    - Is .NET 8 SDK installed?
echo    - Is Android SDK installed?
echo    - Is Python 3.11+ installed?
echo    - Is internet connection available?
echo.
echo See error logs above
echo ================================================================
pause
exit /b 1

:success
echo ================================================================
pause
exit /b 0
