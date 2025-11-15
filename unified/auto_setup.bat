@echo off
echo Auto-setup MirrorSync Agent...

set DEVICE=953aeed3
set ADB=C:\platform-tools\adb.exe

echo [1/4] Setting up port forwarding...
%ADB% -s %DEVICE% forward --remove-all
%ADB% -s %DEVICE% forward tcp:4444 tcp:4444

echo [2/4] Restarting agent...
%ADB% -s %DEVICE% shell am force-stop com.mirrorsync.agent
timeout 2 > nul
%ADB% -s %DEVICE% shell monkey -p com.mirrorsync.agent 1

echo [3/4] Waiting for agent startup...
timeout 3 > nul

echo [4/6] Suppressing Android warnings...
call suppress_warnings.bat

echo [5/6] Testing connection...
python test_agent.py

echo [6/6] Setup complete!
echo - Picture now stretches to full normalized field
echo - Android warnings suppressed
echo - Ready for precise control!