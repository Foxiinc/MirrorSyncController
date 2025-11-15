@echo off
echo ========================================
echo Building MirrorSync Controller (Unified)
echo ========================================

REM Очистка предыдущих сборок
if exist unified\dist rmdir /s /q unified\dist
if exist unified\build rmdir /s /q unified\build

REM Сборка Backend
echo [1/4] Building Backend...
cd src\MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true
if %ERRORLEVEL% neq 0 (
    echo Backend build failed!
    exit /b 1
)
cd ..\..

REM Генерация protobuf для GUI
echo [2/4] Generating protobuf files...
cd gui
python generate_proto.py
if %ERRORLEVEL% neq 0 (
    echo Proto generation failed!
    exit /b 1
)
cd ..

REM Подготовка unified структуры
echo [3/4] Preparing unified structure...
if not exist unified mkdir unified
if not exist unified\gui mkdir unified\gui
if not exist unified\backend mkdir unified\backend

REM Копирование файлов
xcopy gui unified\gui /E /Y /Q
xcopy "src\MirrorSync.Backend\bin\Release\net6.0\win-x64\publish" unified\backend /E /Y /Q

REM Сборка единого exe
echo [4/4] Building unified executable...
cd unified
pip install -r requirements.txt --quiet
pyinstaller MirrorSyncController.spec --clean
if %ERRORLEVEL% neq 0 (
    echo Unified build failed!
    exit /b 1
)
cd ..

echo ========================================
echo Build completed successfully!
echo ========================================
echo Executable: unified\dist\MirrorSyncController.exe
echo Size: ~81MB (includes Backend + GUI + Qt6)
echo ========================================

REM Показать размер файла
dir unified\dist\MirrorSyncController.exe | findstr MirrorSyncController.exe