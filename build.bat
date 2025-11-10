@echo off
echo Building MirrorSync Controller...

REM Build Backend
echo Building Backend...
cd src\MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true
if %ERRORLEVEL% neq 0 (
    echo Backend build failed!
    exit /b 1
)
cd ..\..

REM Generate Python protobuf files
echo Generating Python protobuf files...
cd gui
python generate_proto.py
if %ERRORLEVEL% neq 0 (
    echo Proto generation failed!
    exit /b 1
)

REM Build GUI with PyInstaller
echo Building GUI...
pyinstaller --onedir --windowed --name MirrorSyncGUI main_window.py
if %ERRORLEVEL% neq 0 (
    echo GUI build failed!
    exit /b 1
)
cd ..

REM Build Android APK
echo Building Android APK...
cd android
call gradlew assembleRelease
if %ERRORLEVEL% neq 0 (
    echo Android build failed!
    exit /b 1
)
cd ..

REM Create installer
echo Creating installer...
cd installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
if %ERRORLEVEL% neq 0 (
    echo Installer creation failed!
    exit /b 1
)
cd ..

echo Build completed successfully!
echo Installer created: installer\Output\MirrorSyncController-Setup.exe