@echo off
echo Setting up ADB for MirrorSync...

REM Проверяем наличие ADB
adb version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ADB already installed and working!
    adb devices
    goto :end
)

echo ADB not found in PATH. Checking common locations...

REM Проверяем стандартные пути
set ADB_PATHS=C:\platform-tools\adb.exe;C:\Android\Sdk\platform-tools\adb.exe;%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe

for %%i in (%ADB_PATHS%) do (
    if exist "%%i" (
        echo Found ADB at: %%i
        "%%i" version
        "%%i" devices
        goto :end
    )
)

echo ADB not found! Please install Android SDK Platform Tools.
echo Download from: https://developer.android.com/studio/releases/platform-tools
echo Or run install_adb.bat as Administrator

:end
pause