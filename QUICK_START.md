# MirrorSync Controller - Quick Start

## Что это?

Портативное приложение для синхронного управления 2-20 Android-устройствами с Windows-ПК.

## Быстрый старт

### 1. Подготовка

```bash
cd unified
prepare_build.bat
```

Это проверит все зависимости и соберет Backend если нужно.

### 2. Сборка

```bash
build_all.bat
```

Это создаст портативный exe в `dist/MirrorSyncController/MirrorSyncController.exe`

### 3. Запуск

```bash
run.bat
```

Или просто запустите:
```
dist/MirrorSyncController/MirrorSyncController.exe
```

## Требования

- Windows 10/11 x64
- Python 3.11+
- .NET 8 Runtime
- ADB (опционально, для USB подключения)
- scrcpy (опционально, для зеркалирования)

## Функции

✅ Управление несколькими Android-устройствами  
✅ Синхронное выполнение команд (< 10ms)  
✅ Broadcast режим (команды на все устройства)  
✅ Tap, Swipe, Text, Key команды  
✅ Зеркалирование экранов (scrcpy)  
✅ Портативный exe (все в одном файле)  

## Структура проекта

```
MirrorSyncController/
├── unified/              # Портативная версия (используйте это!)
│   ├── backend/         # Backend executable
│   ├── gui/             # GUI код
│   ├── build_all.bat    # Полная сборка
│   └── run.bat          # Запуск
├── src/                 # Исходный код
│   ├── MirrorSync.Backend/
│   ├── MirrorSync.Protos/
│   └── MirrorSync.GUI/
├── android/             # Android Agent
└── gui/                 # Старая GUI версия
```

## Использование

1. Подключите Android-устройства по USB
2. Включите USB Debugging на каждом устройстве
3. Установите Android Agent APK
4. Включите Accessibility Service
5. Запустите MirrorSyncController.exe
6. Устройства появятся в списке
7. Используйте кнопки для управления

## Troubleshooting

### Устройства не видны
- Проверьте: `adb devices`
- Включите USB Debugging
- Переподключите устройство

### Backend не запускается
- Проверьте порт 50051 свободен
- Убедитесь что .NET 8 Runtime установлен

### GUI не загружается
- Проверьте консоль для ошибок
- Переустановите PyQt6: `pip install --upgrade PyQt6`

## Документация

- [BUILD.md](unified/BUILD.md) - Подробная инструкция сборки
- [README.md](README.md) - Полная документация проекта
- [CONTRIBUTING.md](CONTRIBUTING.md) - Для разработчиков