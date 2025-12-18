# MirrorSync Unified Build Guide

## Структура

```
unified/
├── backend/              # .NET Backend executable
├── gui/                  # PyQt6 GUI
├── main.py              # Launcher
├── requirements.txt     # Python dependencies
├── prepare_build.bat    # Prepare environment
├── build_unified.bat    # Build executable
└── build_all.bat        # Complete build
```

## Требования

- Windows 10/11 x64
- Python 3.11+
- .NET 8 Runtime
- PyInstaller: `pip install pyinstaller`

## Сборка

### Вариант 1: Полная сборка (рекомендуется)

```bash
cd unified
build_all.bat
```

Это выполнит:
1. Проверку зависимостей
2. Сборку Backend (если нужно)
3. Сборку портативного exe

### Вариант 2: Пошаговая сборка

```bash
# Шаг 1: Подготовка
prepare_build.bat

# Шаг 2: Сборка
build_unified.bat
```

## Результат

Портативный exe находится в:
```
unified/dist/MirrorSyncController/MirrorSyncController.exe
```

## Запуск

```bash
dist/MirrorSyncController/MirrorSyncController.exe
```

## Что включено в exe

- ✅ Backend (.NET 8)
- ✅ GUI (PyQt6)
- ✅ Все зависимости Python
- ✅ Проверка ADB/scrcpy при запуске

## Возможные проблемы

### Backend не запускается
- Убедитесь, что `backend/MirrorSync.Backend.exe` существует
- Проверьте, что порт 50051 свободен

### GUI не загружается
- Проверьте логи в консоли
- Убедитесь, что PyQt6 установлен: `pip install PyQt6`

### Зависимости не найдены
- Запустите `prepare_build.bat` для проверки
- Установите недостающие компоненты

## Оптимизация размера

Для уменьшения размера exe:

```bash
pyinstaller --onedir --windowed --name MirrorSyncController ^
    --add-data "gui;gui" ^
    --add-data "backend;backend" ^
    --strip ^
    main.py
```

## Распространение

Папка `dist/MirrorSyncController/` содержит все необходимое для запуска.
Можно скопировать на другой компьютер с Windows 10/11 x64.