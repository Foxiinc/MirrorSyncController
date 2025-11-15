@echo off
echo Installing ADB (Android Debug Bridge)...

REM Создаем папку для ADB
if not exist "C:\platform-tools" mkdir "C:\platform-tools"

REM Скачиваем ADB
echo Downloading ADB...
powershell -Command "& {Invoke-WebRequest -Uri 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip' -OutFile 'platform-tools.zip'}"

REM Распаковываем
echo Extracting ADB...
powershell -Command "& {Expand-Archive -Path 'platform-tools.zip' -DestinationPath '.' -Force}"

REM Копируем файлы
xcopy "platform-tools\*" "C:\platform-tools\" /E /Y

REM Добавляем в PATH
echo Adding to PATH...
setx PATH "%PATH%;C:\platform-tools" /M

REM Очистка
del platform-tools.zip
rmdir /s /q platform-tools

echo ADB installed successfully!
echo Please restart your command prompt to use ADB.
echo Test with: adb version

pause