@echo off
echo Fixing PyQt6 compatibility issues...

REM Переустанавливаем PyQt6 с правильными версиями
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y
pip install PyQt6==6.7.1 --force-reinstall

REM Устанавливаем остальные зависимости
pip install -r requirements.txt

echo PyQt6 fixed! Try running the application again.