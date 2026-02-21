# План разработки: фича «Тап по элементу» и исправления

## Порядок фаз

Сначала исправления (стабильность и чистота кода), затем новая фича. Зависимости между задачами учтены.

---

## Фаза 1 — Критичные исправления (Backend + Android)

### 1.1 Скриншоты по gRPC (п.1)

**Проблема:** Backend шлёт `{"type":"SCREENSHOT"}` по TCP:4444 и ждёт 4 байта + binary. Android обрабатывает только TIME_SYNC, PING и DeviceCommand; SCREENSHOT попадает в else и возвращает JSON.

**Решение:** Реализовать на агенте отдельную обработку SCREENSHOT на порту 4444 (один канал с командами).

| Где | Что сделать |
|-----|-------------|
| **Android** `TcpServerService` | В `handleClient` добавить ветку `line.contains("SCREENSHOT")` (или парсить JSON и проверять `type == "SCREENSHOT"`). Не вызывать `executeCommand`. |
| **Android** | Обработчик SCREENSHOT: получить root from `MirrorAccessibilityService`, сделать снимок экрана (через `AccessibilityService` нет прямого API; использовать **MediaProjection** или вызов из сервиса, у которого уже есть права). Альтернатива: держать в сервисе ссылку на `ScreenStreamService` или общий код захвата (например, через `SurfaceControl` / `MediaProjection`). Проще всего: в `TcpServerService` при SCREENSHOT запросить у `MirrorAccessibilityService` «снимок» — но у Accessibility нет capture. Значит, снимок должен делать сервис с MediaProjection. Проверить: `ScreenStreamService` уже делает `captureScreen()` — вынести захват в общий хелпер (например, `ScreenCaptureHelper`), вызывать из `ScreenStreamService` и из обработчика SCREENSHOT в TCP. По TCP ответ: 4 байта (big-endian length) + JPEG bytes. |
| **Android** | Формат ответа по TCP: после строки-запроса `{"type":"SCREENSHOT"}\n` — сразу писать в сокет 4 байта (size, big-endian) + image bytes. Не писать JSON. |
| **Backend** `AgentConnection.GetScreenshotAsync` | Оставить текущую логику чтения (4 байта + body). После чтения картинки получать реальные размеры (см. п.1.5). |

**Уточнение по захвату экрана на Android:** В проекте захват уже реализован в `ScreenStreamService.captureScreen()` через `Runtime.getRuntime().exec("screencap -p")`. Вынести эту логику в общий хелпер (например, `ScreenCaptureHelper.capture(): Bitmap?`) и вызывать его из `ScreenStreamService` и из обработчика SCREENSHOT в `TcpServerService`. Формат ответа по TCP для SCREENSHOT: 4 байта size (big-endian) + 4 байта width + 4 байта height (big-endian) + JPEG bytes. Размеры брать из `bitmap.width`, `bitmap.height`.

### 1.2 Реальные размеры скриншота в Backend (п.5)

**Проблема:** В `AgentConnection.GetScreenshotAsync()` подставлены `Width = 720`, `Height = 1650`.

**Решение:**

| Где | Что сделать |
|-----|-------------|
| **Android** | В ответе SCREENSHOT после размера картинки можно либо: (A) встроить размер в бинарный протокол (например, 4 байта width + 4 байта height перед JPEG), либо (B) декодировать JPEG на агенте и взять width/height из Bitmap. Вариант B проще: после `captureScreen()` использовать `bitmap.width`, `bitmap.height` и передать в протокол (см. ниже). |
| **Протокол TCP** | Расширить ответ SCREENSHOT: например `[4 bytes size][4 bytes width][4 bytes height][JPEG data]` (все big-endian). Тогда backend читает 4+4+4, потом size байт. Либо один раз передать размеры в JSON перед бинарем — усложняет парсинг. Проще: 4 (size) + 4 (width) + 4 (height) + image. |
| **Backend** | В `GetScreenshotAsync` после чтения 4 байт size прочитать ещё 8 байт (width, height), затем image size байт. Заполнять `ScreenshotData.Width` и `Height` из этих значений. |

Итог: договориться о формате с агентом (например 4+4+4+image) и реализовать на обеих сторонах.

### 1.3 ConnectionPool и владение соединениями (п.2)

**Проблема:** `ConnectionPool` зарегистрирован в DI, но не используется; `DeviceManager` сам держит `_connections` и создаёт `AgentConnection`.

**Решение:** Один источник правды — пул соединений.

| Где | Что сделать |
|-----|-------------|
| **Backend** | `DeviceManager` не должен создавать и хранить `AgentConnection` сам. Инжектировать `ConnectionPool`. В `SetupPortForwardAsync` после порт-форварда вызывать `_connectionPool.GetOrCreateConnectionAsync(androidDevice)` и не хранить соединения в `DeviceManager`. |
| **DeviceManager** | Для `SendCommandAsync`, `GetScreenshotAsync` брать соединение через `_connectionPool.GetOrCreateConnectionAsync(device)` (или метод вида `GetConnection(serial)` на пуле). При отключении устройства вызывать `_connectionPool.RemoveConnection(serial)`. |
| **ConnectionPool** | Убедиться, что API пула покрывает сценарии: получить соединение по serial, удалить при отключении. При необходимости добавить метод `GetConnection(string serial)` (возвращать null если нет). |
| **Program.cs** | Оставить регистрацию `ConnectionPool`. В `DeviceManager` инжектировать `ConnectionPool` и использовать его вместо `_connections`. Удалить из `DeviceManager` поле `_connections` и всю логику создания `AgentConnection` внутри менеджера. |

### 1.4 Хост и порт агента из конфига (п.3)

**Проблема:** В `AgentConnection` зашиты `127.0.0.1` и `4444`.

**Решение:**

| Где | Что сделать |
|-----|-------------|
| **MirrorSyncConfig** | Уже есть `AgentPort` (4444). Добавить `AgentHost` (по умолчанию `"127.0.0.1"`). |
| **DeviceManager** | При создании соединения (через пул) передавать устройство; пул/коннекшен должны знать хост и порт. Поскольку порт-форвард всегда на 4444 на локальной стороне, хост = 127.0.0.1, порт = 4444 — но брать их из конфига. |
| **ConnectionPool / AgentConnection** | Конфиг инжектировать в пул и в `AgentConnection`. В `AgentConnection.ConnectAsync()` использовать `_config.AgentHost` и `_config.AgentPort` вместо констант. |

Учесть: порт-форвард в `DeviceManager.SetupPortForwardAsync` тоже использует 4444 — оставить согласованным с конфигом (один порт на все устройства за форвардом).

### 1.5 Поиск ADB на Linux/macOS (п.4)

**Проблема:** `FindAdbPath()` только Windows-пути; при `linux-x64` ADB не находится.

**Решение:**

| Где | Что сделать |
|-----|-------------|
| **DeviceManager** (или вынести в `AdbPathResolver`) | Сначала проверять конфиг: если `MirrorSyncConfig.AdbPaths` не пустой — перебирать их. Затем искать в PATH: `Environment.GetEnvironmentVariable("PATH")`, разбить по `:` (Linux/Mac) или `;` (Windows), в каждой папке искать `adb` или `adb.exe`. Затем добавить типичные пути: Linux — `~/Android/Sdk/platform-tools/adb`, `/usr/bin/adb`; macOS — `~/Library/Android/sdk/platform-tools/adb`. Использовать `RuntimeInformation.IsOSPlatform(OSPlatform.Windows)` для выбора расширения `.exe`. |

### 1.6 Убрать вводящий в заблуждение _nextPort (п.6)

**Проблема:** `_nextPort++` создаёт впечатление разного порта на устройство; везде используется один 4444.

**Решение:**

| Где | Что сделать |
|-----|-------------|
| **DeviceManager** | Удалить поле `_nextPort`. В `GetOrAdd(device.Serial, ...)` задавать `Port = 4444` (или брать из конфига `AgentPort`). Если позже понадобится разный порт на устройство — вводить отдельно. |

---

## Фаза 2 — Качество кода и мелкие доработки

### 2.1 Пустой catch и подавление ошибок (п.9)

| Файл | Что сделать |
|------|-------------|
| **DeviceManager.StopMirror** | В `catch` логировать: `_logger.LogWarning(ex, "Failed to kill mirror process for {Serial}", serial);` |
| **Python** `ScreenshotService.reconnect` | В `except` логировать: `print(f"Reconnect error: {e}")` или `logging.warning("Reconnect error: %s", e)`. Не использовать голый `except: pass`. |

### 2.2 Дублирование проверки Accessibility (п.10)

| Где | Что сделать |
|-----|-------------|
| **MainActivity** | Оставить один способ проверки. Удалить дубликат: оставить метод, который использует `AccessibilityManager.getEnabledAccessibilityServiceList` (актуальный список), и вызывать его из `updateStatus()`. Статический `isAccessibilityServiceEnabled(context)` в companion убрать или сделать обёрткой над общим методом с передачей context. |

---

## Фаза 3 — Стрим скриншотов (Python) и TEXT

### 3.1 Python ScreenshotService и порт 8080 (п.7)

**Проблема:** Стрим на 8080 не привязан к устройству; при нескольких устройствах нужен порт-форвард на каждый; в GUI стрим отключён (`pass`).

**Решение:**

| Где | Что сделать |
|-----|-------------|
| **Backend** | Не обязательно поднимать прокси стрима в бэкенде: GUI может работать через adb port-forward, который пользователь/скрипт поднимает для выбранного устройства (например `adb -s SERIAL forward tcp:8080 tcp:8080`). Документировать это. |
| **Python** `ScreenshotService` | Принимать `serial` и `local_port`: для одного устройства local_port=8080; при нескольких — вызывающая сторона (GUI) должна поднимать форвард на разные локальные порты (8080, 8081, …) и передавать в сервис `port=8080` для первого, `8081` для второго и т.д. |
| **unified/gui** | В `PhoneScreen.start_screenshot_service()`: если нужен живой стрим — создавать `ScreenshotService(serial=self.device_serial, port=...)`. Порт брать из конфига или из маппинга serial→port (например, backend может отдавать для каждого устройства порт стрима, если решите поднимать форварды из бэкенда). Минимальный вариант: один девайс — порт 8080, в GUI включить вызов и отображение кадра в `update_screenshot`. |

### 3.2 performText (п.8)

**Проблема:** TEXT не реализован, возвращает false.

**Решение (один из вариантов):**

| Где | Что сделать |
|-----|-------------|
| **Android** `MirrorAccessibilityService.performText` | Найти фокусный узел (focused node или root и поиск editable). Вызвать `node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT)` с `Bundle` и текстом (API 21+). Либо вставить через Clipboard: скопировать текст в буфер, затем на узле выполнить ACTION_PASTE. Если фокуса нет — искать первый подходящий editable и выполнять setText на нём. При неудаче возвращать false и логировать. |

Либо явно пометить в API/UI, что TEXT пока не поддерживается, и не обещать ввод текста.

---

## Фаза 4 — Автотесты (п.11)

| Область | Что сделать |
|---------|-------------|
| **Backend** | Добавить проект тестов (xUnit или NUnit). Тесты: парсинг/сериализация `DeviceCommand` в JSON; логика `DeviceManager` (например, ScanDevicesAsync мок ADB); вызовы gRPC (интеграционные с тестовым хостом) — по желанию. |
| **Android** | Юнит-тесты для `CoordinateNormalizer` (normalizedToPixels для известных разрешений), `GestureValidator` (валидные/невалидные tap/swipe). Инструментальные тесты при необходимости. |
| **Proto** | При регенерации — убедиться, что контракт не сломан; при желании тест на то, что все RPC вызываются без исключений с пустыми запросами. |

---

## Фаза 5 — Фича: тап по элементу, свайпы без изменений

### 5.1 Контракт (Proto + модели)

| Где | Что сделать |
|-----|-------------|
| **device_control.proto** | В `CommandRequest` добавить опциональные поля для тапа по элементу, например: `string tap_view_id = 10;` (resource-id), `string tap_text = 11;`, `string tap_content_desc = 12;`. Либо oneof `tap_target { string view_id; string text; string content_desc; }` и оставить x,y для fallback/координатного тапа. |
| **Backend** | Регенерация proto; в `DeviceCommand` (или в DTO для агента) добавить поля для селектора. При отправке на агент передавать и координаты (если есть), и селектор (если есть). |
| **Android** `DeviceCommand` | Добавить поля `tapViewId`, `tapText`, `tapContentDesc` (nullable). Логика: если передан селектор — тап по элементу; иначе — по (x, y) как сейчас. |

### 5.2 Android: поиск узла и тап по нему

| Где | Что сделать |
|-----|-------------|
| **MirrorAccessibilityService** | Реализовать `findNode(viewId: String?, text: String?, contentDesc: String?): AccessibilityNodeInfo?`: обход корня `getRootInActiveWindow()`, рекурсивно по детям, сравнение `viewIdResourceName`, `text`, `contentDescription`. Вернуть первый подходящий кликабельный/фокусируемый узел или первый с совпадением. |
| **MirrorAccessibilityService** | Добавить `performTapOnNode(node: AccessibilityNodeInfo): Boolean`: получить `Rect` из `getBoundsInScreen()`, центр rect, затем `dispatchGesture` в эту точку (или попробовать `node.performAction(ACTION_CLICK)`). |
| **executeCommand** | Для типа TAP: если задан селектор (viewId/text/contentDesc) — вызвать `findNode` и `performTapOnNode`; иначе — текущая логика по нормализованным (x, y). SWIPE не менять (оставить нормализованные координаты). |

### 5.3 Backend и GUI

| Где | Что сделать |
|-----|-------------|
| **DeviceControlService.SendCommand** | Принимать из gRPC новые поля; при формировании команды для агента подставлять селектор, если клиент его передал. |
| **Python / C# GUI** | Опционально: в UI тапа добавить режим «по элементу» и поле ввода resource-id / text / content-desc; при отправке заполнять соответствующие поля запроса. Для первой итерации достаточно поддержки в proto и агенте; GUI можно расширить позже. |

### 5.4 Обратная совместимость

- Старые клиенты продолжают слать только x, y для TAP — агент ведёт себя как сейчас (тап по координатам).
- Новые клиенты могут передавать только селектор или селектор + координаты (fallback, если узел не найден — по желанию можно сделать тап по x,y).

---

## Краткий чеклист по фазам

- **Фаза 1:** 1.1 SCREENSHOT на агенте + формат ответа → 1.2 размеры в ответе + чтение в backend → 1.3 ConnectionPool как единственный владелец соединений → 1.4 Host/port из конфига → 1.5 ADB Linux/Mac → 1.6 убрать _nextPort.
- **Фаза 2:** 2.1 логи в catch, 2.2 одна проверка Accessibility.
- **Фаза 3:** 3.1 Python стрим + порт по устройству, 3.2 performText или явное «не поддерживается».
- **Фаза 4:** тесты backend + Android (нормализация, валидация).
- **Фаза 5:** proto + агент (findNode, tap by node) + backend передача полей + опционально GUI.

Гит и удалённые файлы (п.12) по твоему решению не трогаем.
