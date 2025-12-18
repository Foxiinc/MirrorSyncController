# 🚀 Руководство по сборке и тестированию

## 📋 Быстрый старт

### Вариант 1: Автоматическая сборка и тест (Рекомендуется)

```cmd
# 1. Полная сборка всех компонентов
BUILD_AND_TEST.bat

# 2. Установка и настройка на устройстве
TEST_SYSTEM.bat

# 3. Быстрая проверка статуса
QUICK_TEST.bat
```

---

## 🔧 Вариант 2: Ручная сборка

### Шаг 1: Backend (.NET 8)

```cmd
cd src\MirrorSync.Backend

# Очистка
dotnet clean

# Восстановление зависимостей
dotnet restore

# Сборка
dotnet build -c Release

# Публикация
dotnet publish -c Release -r win-x64 --self-contained false

cd ..\..
```

**Результат:** `src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish\MirrorSync.Backend.exe`

---

### Шаг 2: Android APK

```cmd
cd android

# Очистка
gradlew.bat clean

# Сборка Release
gradlew.bat assembleRelease

cd ..
```

**Результат:** `android\app\build\outputs\apk\release\app-release.apk`

---

### Шаг 3: Python GUI

```cmd
cd gui

# Установка зависимостей
pip install -r requirements.txt

# Генерация protobuf (если нужно)
python generate_proto.py

cd ..
```

---

## 📱 Установка на устройство

### 1. Подключение устройства

```cmd
# Проверка подключения
adb devices

# Должно показать:
# List of devices attached
# XXXXXXXXXX    device
```

### 2. Установка APK

```cmd
# Установка (или переустановка)
adb install -r android\app\build\outputs\apk\release\app-release.apk
```

### 3. Настройка Accessibility Service

**На устройстве:**
1. Откройте "MirrorSync Agent"
2. Нажмите "Open Accessibility Settings"
3. Найдите "MirrorSync Agent"
4. Включите переключатель
5. Подтвердите в диалоге

**Для Android 13+:**
1. Settings → Apps → MirrorSync Agent
2. Три точки (⋮) → Allow restricted settings
3. Включите переключатель
4. Затем включите Accessibility Service

### 4. Port Forwarding

```cmd
# Настройка forwarding
adb forward tcp:4444 tcp:4444

# Проверка
adb forward --list
# Должно показать: XXXX tcp:4444 tcp:4444
```

---

## 🚀 Запуск системы

### Терминал 1: Backend

```cmd
cd src\MirrorSync.Backend\bin\Release\net8.0\win-x64\publish
MirrorSync.Backend.exe
```

**Ожидаемый вывод:**
```
[12:34:56 INF] MirrorSync Backend starting on port 50051
[12:34:56 INF] Application started. Press Ctrl+C to shut down.
```

### Терминал 2: GUI

```cmd
cd gui
python main_window.py
```

**Ожидаемое поведение:**
- Окно GUI открывается
- Нажмите "Refresh"
- Устройство появляется в списке

---

## 🧪 Тестирование

### Тест 1: Проверка подключения

**В GUI:**
1. Нажмите "Refresh"
2. Устройство должно появиться в таблице
3. Статус: "connected"
4. Agent: "✓"

**На устройстве:**
1. Откройте MirrorSync Agent
2. Статус должен быть:
   - ✅ Accessibility Service: RUNNING
   - ✅ TCP Server: Listening on port 4444

### Тест 2: Простой TAP

**В GUI:**
1. Выберите устройство (кликните на строку)
2. Установите Tap X: 50 (центр по горизонтали)
3. Установите Tap Y: 50 (центр по вертикали)
4. Нажмите "Tap"

**На устройстве:**
- Должен произойти тап в центре экрана
- Если открыто приложение - может что-то нажаться

**В логах (View Logs на устройстве):**
```
12:34:56.789 D/MirrorAccessibilityService: TAP (0.5, 0.5)
12:34:56.840 I/MirrorAccessibilityService: TAP seq=1 ✓ 51ms
```

### Тест 3: Swipe

**В GUI:**
1. Установите Swipe X1: 20 (левая часть)
2. Установите Swipe X2: 80 (правая часть)
3. Нажмите "Swipe"

**На устройстве:**
- Должен произойти свайп слева направо
- Если на главном экране - может переключить страницу

### Тест 4: Broadcast Mode

**В GUI:**
1. Подключите 2+ устройства
2. Включите "Broadcast Mode"
3. Нажмите "Tap"

**На всех устройствах:**
- Тап должен произойти одновременно (±10ms)

---

## 🔍 Диагностика проблем

### Проблема: Backend не запускается

**Проверка:**
```cmd
dotnet --version
# Должно быть: 8.0.x
```

**Решение:**
- Установите .NET 8 SDK
- Пересоберите проект

### Проблема: Устройство не появляется в GUI

**Проверка:**
```cmd
adb devices
adb forward --list
```

**Решение:**
1. Проверьте USB подключение
2. Включите USB Debugging
3. Настройте port forwarding: `adb forward tcp:4444 tcp:4444`
4. Перезапустите Backend

### Проблема: Accessibility Service не включается

**Для Android 13+:**
1. Settings → Apps → MirrorSync Agent
2. ⋮ → Allow restricted settings
3. Включите
4. Затем включите Accessibility Service

**Для всех версий:**
1. Переустановите APK
2. Перезагрузите устройство
3. Попробуйте снова

### Проблема: Жесты не выполняются

**Проверка логов:**
```cmd
adb logcat -s InAppLogger:* -v time
```

**Ожидаемые логи:**
```
12:34:56.789 I/TcpServerService: Client connected
12:34:57.123 D/TcpServerService: PING -> PONG
12:34:58.456 D/MirrorAccessibilityService: TAP (0.5, 0.5)
12:34:58.507 I/MirrorAccessibilityService: TAP seq=1 ✓ 51ms
```

**Если нет логов TAP:**
- Проверьте что Accessibility Service включен
- Проверьте координаты (должны быть 0.0-1.0)
- Перезапустите приложение

### Проблема: Координаты неправильные

**Проверка:**
```cmd
adb logcat -s CoordinateNormalizer:* -v time
```

**Ожидаемый вывод:**
```
12:34:56.789 D/CoordinateNormalizer: Screen: 1080x2400, density=3.0
12:34:57.123 D/CoordinateNormalizer: Normalized (0.5, 0.5) -> Pixels (540.0, 1200.0)
```

**Решение:**
- Координаты автоматически нормализуются
- Используйте значения 0.0-1.0 в GUI
- Проверьте что устройство не в landscape режиме

---

## 📊 Метрики производительности

### Целевые показатели:

| Метрика | Целевое значение | Как проверить |
|---------|------------------|---------------|
| Задержка команды | < 50ms | Логи Android: "TAP seq=X ✓ XXms" |
| Синхронизация | < 10ms между устройствами | Broadcast mode + секундомер |
| Успешность | > 95% | Логи: соотношение ✓ к ✗ |
| Точность тапа | ±5 пикселей | Визуальная проверка |

### Измерение задержки:

**В логах Android:**
```
I/MirrorAccessibilityService: TAP seq=1 ✓ 52ms
                                           ^^^^
                                           Время выполнения
```

**Компоненты задержки:**
- GUI → Backend: ~5ms (gRPC)
- Backend → Android: ~10ms (TCP)
- Android обработка: ~5ms
- Выполнение жеста: ~30ms
- **Итого:** ~50ms

---

## 🎯 Чеклист готовности

### Перед тестированием:

- [ ] .NET 8 SDK установлен
- [ ] Android SDK установлен
- [ ] Python 3.11+ установлен
- [ ] ADB в PATH
- [ ] Устройство подключено по USB
- [ ] USB Debugging включен

### После сборки:

- [ ] Backend.exe существует
- [ ] app-release.apk существует
- [ ] Python зависимости установлены
- [ ] Backend запускается без ошибок
- [ ] GUI открывается

### На устройстве:

- [ ] APK установлен
- [ ] Accessibility Service включен
- [ ] Статусы показывают ✅
- [ ] Port forwarding настроен
- [ ] Логи отображаются

### Функциональность:

- [ ] Устройство появляется в GUI
- [ ] TAP работает
- [ ] SWIPE работает
- [ ] Broadcast mode работает (2+ устройств)
- [ ] Логи отображаются в приложении
- [ ] Share логов работает

---

## 🚀 Готово к использованию!

Если все чеклисты пройдены - система полностью готова к работе.

**Следующие шаги:**
1. Протестируйте на разных устройствах
2. Проверьте синхронизацию с 2+ устройствами
3. Измерьте производительность
4. Соберите feedback

**Документация:**
- `COORDINATE_NORMALIZATION_GUIDE.md` - Нормализация координат
- `ANDROID_IMPLEMENTATION_COMPLETE.md` - Android исправления
- `IN_APP_LOGGER_COMPLETE.md` - Встроенный логгер
- `IMPLEMENTATION_REPORT.md` - Общий отчет

**Поддержка:**
- Логи Backend: Консоль Backend
- Логи Android: Приложение → View Logs
- Логи ADB: `adb logcat -s InAppLogger:*`
