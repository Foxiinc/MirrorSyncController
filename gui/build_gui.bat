@echo off
echo Building MirrorSync GUI...

REM Generate protobuf files
echo Generating protobuf files...
python generate_proto.py
if %ERRORLEVEL% neq 0 (
    echo Proto generation failed!
    exit /b 1
)

REM Build with PyInstaller
echo Building executable...
pyinstaller --onedir --windowed --name MirrorSyncGUI --icon=icon.ico main.py
if %ERRORLEVEL% neq 0 (
    echo PyInstaller build failed!
    exit /b 1
)

echo GUI build completed successfully!
echo Executable: dist\MirrorSyncGUI\MirrorSyncGUI.exe