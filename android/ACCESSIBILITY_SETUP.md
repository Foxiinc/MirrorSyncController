# Настройка Accessibility Service для MirrorSync Agent

## Общие требования

1. **Android 7.0+ (API 24+)** - минимальная версия
2. **USB Debugging включен** в Developer Options
3. **Установка из неизвестных источников** разрешена (для APK)

## Пошаговая настройка

### Шаг 1: Установка приложения
```bash
adb install app-release.apk
```

### Шаг 2: Запуск приложения
1. Найдите "MirrorSync Agent" в списке приложений
2. Запустите приложение
3. Нажмите кнопку "Enable Accessibility Service"

### Шаг 3: Включение Accessibility Service

#### Для Android 7-12:
1. Откроется Settings → Accessibility
2. Найдите "MirrorSync Agent" в списке сервисов
3. Нажмите на него и включите переключатель
4. Подтвердите в диалоге безопасности

#### Для Android 13+ (ВАЖНО - Restricted Settings):
1. **СНАЧАЛА** разрешите Restricted Settings:
   - Settings → Apps → MirrorSync Agent
   - Нажмите три точки (⋮) → "Allow restricted settings"
   - Включите переключатель
   
2. **ЗАТЕМ** включите Accessibility Service:
   - Settings → Accessibility → MirrorSync Agent
   - Включите переключатель
   - Подтвердите в диалоге

## Проверка работоспособности

### В приложении MirrorSync Agent:
- Статус должен показывать "MirrorSync Agent is running"
- Кнопка "Enable" должна быть неактивна

### Через ADB:
```bash
# Проверить, что сервис включен
adb shell settings get secure enabled_accessibility_services

# Должно содержать: com.mirrorsync.agent/.MirrorAccessibilityService
```

### Через логи:
```bash
adb logcat | grep MirrorAccessibilityService
# Должно показать: "Accessibility service connected"
```

## Устранение проблем

### Проблема: Сервис не включается
**Решение:**
1. Убедитесь, что разрешены Restricted Settings (Android 13+)
2. Перезагрузите устройство
3. Переустановите приложение

### Проблема: "Cannot perform gestures"
**Решение:**
1. Проверьте, что в настройках Accessibility включен именно MirrorSync Agent
2. Убедитесь, что приложение имеет все необходимые разрешения
3. Проверьте логи на ошибки конфигурации

### Проблема: Restricted Settings недоступны
**Решение:**
1. Убедитесь, что используется Android 13+
2. Попробуйте установить APK через ADB с флагом `-g`:
   ```bash
   adb install -g app-release.apk
   ```
3. Вручную перейдите в App Info через Settings

## Безопасность

### Что делает Accessibility Service:
- ✅ Выполняет жесты (tap, swipe) по командам с ПК
- ✅ Работает только при активном TCP соединении
- ❌ НЕ читает содержимое экрана
- ❌ НЕ записывает данные
- ❌ НЕ отправляет информацию в интернет

### Разрешения:
- `BIND_ACCESSIBILITY_SERVICE` - для работы сервиса
- `INTERNET` - для TCP соединения с ПК
- `FOREGROUND_SERVICE` - для стабильной работы

## Технические детали

### Конфигурация сервиса:
```xml
<accessibility-service
    android:accessibilityEventTypes="typeWindowStateChanged|typeWindowContentChanged"
    android:accessibilityFlags="flagDefault|flagRetrieveInteractiveWindows"
    android:canPerformGestures="true"
    android:canRetrieveWindowContent="true" />
```

### Поддерживаемые команды:
- `TAP` - одиночное нажатие по координатам (0-1)
- `SWIPE` - свайп между двумя точками
- `TEXT` - ввод текста (планируется)
- `KEY` - нажатие клавиш (планируется)

## Автоматизация настройки

Для массовой настройки устройств можно использовать:

```bash
# Скрипт автоматической настройки
adb install -g app-release.apk
adb shell am start -n com.mirrorsync.agent/.MainActivity
adb shell am start -a android.settings.ACCESSIBILITY_SETTINGS
```

**Примечание:** Включение Accessibility Service всё равно требует ручного подтверждения пользователем по соображениям безопасности Android.