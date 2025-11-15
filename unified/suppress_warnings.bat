@echo off
echo Suppressing Android warnings and developer options...

set DEVICE=953aeed3
set ADB=C:\platform-tools\adb.exe

echo [1/5] Disabling developer options warnings...
%ADB% -s %DEVICE% shell settings put global development_settings_enabled 0

echo [2/5] Hiding developer options...
%ADB% -s %DEVICE% shell settings put global adb_enabled 0
%ADB% -s %DEVICE% shell settings put global adb_enabled 1

echo [3/5] Suppressing security warnings...
%ADB% -s %DEVICE% shell settings put secure install_non_market_apps 1
%ADB% -s %DEVICE% shell settings put global package_verifier_enable 0

echo [4/5] Disabling system UI warnings...
%ADB% -s %DEVICE% shell settings put global heads_up_notifications_enabled 0
%ADB% -s %DEVICE% shell settings put system notification_light_pulse 0

echo [5/5] Hiding navigation bar warnings...
%ADB% -s %DEVICE% shell wm overscan 0,0,0,0

echo Warnings suppressed! Restart the device for full effect.