# MirrorSync Controller

**Полная система синхронного управления Android-устройствами с Windows-ПК**

Система обеспечивает зеркалирование экранов и синхронное управление 2-20 Android устройствами с точностью < 10ms.

## Архитектура

- **Backend**: .NET 8 (C#) - Windows service для управления устройствами через ADB
- **GUI**: Python 3.11 + PyQt6 - интерфейс пользователя
- **Android Agent**: Kotlin + AccessibilityService - агент на Android устройствах
- **Installer**: Inno Setup - установщик для Windows

## Требования

### Windows (Backend + GUI)
- Windows 10/11 x64
- .NET 8 Runtime
- Python 3.11
- ADB (Android Debug Bridge)
- scrcpy для зеркалирования экранов

### Android (Agent)
- Android 7.0+ (API 24+)
- Разрешения: Accessibility Service, Internet

## Сборка проекта

### Подготовка окружения

1. Установите .NET 8 SDK
2. Установите Python 3.11 и pip
3. Установите Android SDK и настройте ADB
4. Скачайте scrcpy

### Установка зависимостей

```bash
# Python зависимости
cd gui
pip install -r requirements.txt

# .NET зависимости (автоматически при сборке)
```

### Сборка

Запустите `build.bat` для автоматической сборки всех компонентов:

```cmd
build.bat
```

Или собирайте компоненты по отдельности:

```bash
# Backend
cd src\MirrorSync.Backend
dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true

# GUI
cd gui
python generate_proto.py
pyinstaller --onedir --windowed --name MirrorSyncGUI main_window.py

# Android
cd android
gradlew assembleRelease
```

## Установка и настройка

### Windows

1. Запустите `installer\Output\MirrorSyncController-Setup.exe`
2. Следуйте инструкциям установщика
3. Backend автоматически установится как Windows Service

### Android

1. Установите APK: `android\app\build\outputs\apk\release\app-release.apk`
2. Откройте приложение MirrorSync Agent
3. Включите Accessibility Service в настройках Android
4. Подключите устройство по USB и включите USB Debugging

## Использование

### Запуск системы

1. Убедитесь, что Backend service запущен (автоматически после установки)
2. Запустите GUI: MirrorSync Controller
3. Подключите Android устройства по USB
4. Устройства появятся в списке GUI

### Основные функции

- **Список устройств**: отображение подключенных Android устройств
- **Broadcast Mode**: отправка команд на все устройства одновременно
- **Tap**: отправка тапов по координатам (нормализованные 0-1)
- **Swipe**: отправка свайпов между двумя точками
- **Text**: отправка текста на устройства
- **Mirror**: запуск зеркалирования экрана через scrcpy

### Синхронизация

Система обеспечивает синхронизацию команд с точностью до 10ms:

1. Backend синхронизирует время с каждым агентом
2. Команды отправляются с рассчитанным временем выполнения
3. Агенты ждут до назначенного времени и выполняют команды синхронно

## Протоколы связи

### gRPC (GUI ↔ Backend)
- Порт: 50051
- Сервисы: ListDevices, SendCommand, StartMirror, StopMirror

### TCP JSON (Backend ↔ Agent)
- Порт: 4444 (через ADB port forwarding)
- Команды: TAP, SWIPE, TEXT, KEY, TIME_SYNC

## Структура проекта

```
MirrorSyncController/
├── src/
│   ├── MirrorSync.Backend/     # .NET Backend
│   └── MirrorSync.Protos/      # gRPC протоколы
├── gui/                        # PyQt GUI
├── android/                    # Android Agent
├── installer/                  # Inno Setup
└── build.bat                   # Скрипт сборки
```

## Тестирование

### Unit тесты

```bash
# Backend тесты
cd src\MirrorSync.Backend.Tests
dotnet test

# GUI тесты
cd gui
python -m pytest tests/
```

### Нагрузочное тестирование

1. Подключите максимальное количество устройств (до 20)
2. Включите Broadcast Mode
3. Отправляйте команды с высокой частотой
4. Мониторьте синхронизацию через логи

## Troubleshooting

### Backend не запускается
- Проверьте, что .NET 8 Runtime установлен
- Убедитесь, что порт 50051 свободен
- Проверьте логи в `logs/mirrorsync-*.txt`

### Устройства не подключаются
- Убедитесь, что ADB работает: `adb devices`
- Проверьте USB Debugging на Android
- Перезапустите ADB server: `adb kill-server && adb start-server`

### Агент не отвечает
- Убедитесь, что Accessibility Service включен
- Проверьте, что приложение MirrorSync Agent запущено
- Проверьте port forwarding: `adb forward --list`

## Тестирование системы

### Автоматическое тестирование

Запустите системный тест для проверки всех компонентов:

```cmd
python test_system.py
```

### Пошаговое тестирование

1. **Сборка проекта**:
   ```cmd
   build.bat
   ```

2. **Запуск Backend**:
   ```cmd
   src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\MirrorSync.Backend.exe
   ```

3. **Подключение Android устройства**:
   - Включите USB Debugging
   - Подключите по USB
   - Проверьте: `adb devices`

4. **Установка Android Agent**:
   ```cmd
   adb install android\app\build\outputs\apk\release\app-release.apk
   ```

5. **Настройка Accessibility Service**:
   - Откройте MirrorSync Agent на Android
   - Перейдите в Settings → Accessibility
   - Включите MirrorSync Agent

6. **Запуск GUI**:
   ```cmd
   gui\dist\MirrorSyncGUI\MirrorSyncGUI.exe
   ```

7. **Тестирование синхронизации**:
   - Подключите 2+ устройства
   - Включите Broadcast Mode
   - Отправьте команды Tap/Swipe
   - Проверьте синхронное выполнение

### Нагрузочное тестирование

```python
# Тест синхронизации с множественными устройствами
from gui.backend_client import BackendClient
import time

client = BackendClient()
client.connect()

# Отправка 100 команд с интервалом 50ms
for i in range(100):
    client.send_command("TAP", 0.5, 0.5)
    time.sleep(0.05)
```

### Метрики производительности

- **Точность синхронизации**: < 10ms между устройствами
- **Пропускная способность**: до 20 команд/сек на устройство
- **Максимальные устройства**: 20 одновременно
- **Задержка команды**: < 50ms от GUI до выполнения

## Unit тесты

### Backend тесты

```cmd
cd src\MirrorSync.Backend.Tests
dotnet test
```

### GUI тесты

```cmd
cd gui
python -m pytest tests/
```

### Android тесты

```cmd
cd android
.\gradlew test
```

## Производственное развертывание

1. **Установка через инсталлятор**:
   ```cmd
   installer\Output\MirrorSyncController-Setup.exe
   ```

2. **Проверка службы**:
   ```cmd
   sc query "MirrorSync Backend"
   ```

3. **Мониторинг логов**:
   - Backend: `%ProgramFiles%\MirrorSync\Backend\logs\`
   - GUI: `%APPDATA%\MirrorSync\logs\`

## Лицензия

Проект разработан для внутреннего использования.

---

## Итоговая архитектура

```
┌─────────────────┐    gRPC     ┌──────────────────┐
│   PyQt6 GUI    │◄──────────►│  .NET Backend    │
│  (Port 50051)  │             │   (Service)      │
└─────────────────┘             └──────────────────┘
                                          │
                                          │ ADB + TCP
                                          ▼
                                ┌──────────────────┐
                                │ Android Devices  │
                                │ (Agent + scrcpy) │
                                └──────────────────┘
```

**Ключевые особенности реализации**:
- ✅ Суб-10ms синхронизация через NTP-стиль time sync
- ✅ Поддержка до 20 устройств одновременно
- ✅ Зеркалирование через scrcpy интеграцию
- ✅ Windows Service для стабильной работы
- ✅ Полный инсталлятор с автоматической настройкой
- ✅ Производительный gRPC + TCP стек
- ✅ AccessibilityService для точных жестов