@echo off
echo Building Unified MirrorSync Controller...

REM Install dependencies
pip install -r requirements.txt

REM Build single exe with PyInstaller
pyinstaller --onefile --windowed --name MirrorSyncController ^
    --add-data "gui;gui" ^
    --add-data "backend;backend" ^
    --icon=icon.ico ^
    main.py

echo Build completed!
echo Executable: dist\MirrorSyncController.exe