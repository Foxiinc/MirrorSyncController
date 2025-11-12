@echo off
echo Fixing ADB path issues...

REM Проверяем стандартные пути ADB
set ADB_FOUND=0

if exist "C:\platform-tools\adb.exe" (
    echo Found ADB at C:\platform-tools\
    set ADB_PATH=C:\platform-tools
    set ADB_FOUND=1
)

if exist "C:\Android\Sdk\platform-tools\adb.exe" (
    echo Found ADB at C:\Android\Sdk\platform-tools\
    set ADB_PATH=C:\Android\Sdk\platform-tools
    set ADB_FOUND=1
)

if exist "%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe" (
    echo Found ADB at %USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\
    set ADB_PATH=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools
    set ADB_FOUND=1
)

if %ADB_FOUND%==1 (
    echo Adding %ADB_PATH% to PATH for this session...
    set PATH=%PATH%;%ADB_PATH%
    
    echo Testing ADB...
    adb version
    adb devices
) else (
    echo ADB not found! Please install Android SDK Platform Tools.
    echo Download from: https://developer.android.com/studio/releases/platform-tools
)

echo.
echo Current session PATH updated. To make permanent, add to system PATH manually.
pause