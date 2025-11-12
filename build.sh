#!/bin/bash
set -e

echo "Building MirrorSync Controller..."

# Backend (.NET)
echo "Building Backend..."
cd src/MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true
cd ../..

# GUI (Python)
echo "Building GUI..."
cd gui
python3 generate_proto.py
pip3 install -r requirements.txt
pyinstaller --onedir --windowed --name MirrorSyncGUI main_window.py
cd ..

# Android
echo "Building Android..."
cd android
./gradlew assembleRelease
cd ..

echo "Build completed!"