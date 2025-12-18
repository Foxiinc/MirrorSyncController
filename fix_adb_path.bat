@echo off
echo Adding ADB to PATH for current session...

set "ADB_PATH=C:\Users\foxi\AppData\Local\Android\Sdk\platform-tools"
set "PATH=%PATH%;%ADB_PATH%"

echo ADB path added: %ADB_PATH%
echo Testing ADB...
adb version

echo.
echo ADB is now available in current session.
echo To make permanent, add to system PATH:
echo %ADB_PATH%
echo.

REM Запускаем GUI с правильным PATH
echo Starting GUI with ADB in PATH...
cd unified
python main.py