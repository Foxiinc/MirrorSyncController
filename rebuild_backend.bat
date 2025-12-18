@echo off
echo Rebuilding Backend...

cd src\MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true -o ..\..\unified\backend

if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed
    cd ..\..
    exit /b 1
)

cd ..\..
echo Backend rebuilt successfully!
echo Location: unified\backend\MirrorSync.Backend.exe