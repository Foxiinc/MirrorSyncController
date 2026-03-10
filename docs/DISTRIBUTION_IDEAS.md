# Идеи: один бинарь / дистрибутив MirrorSync Controller

Состав проекта:
- **Backend** — .NET 6, gRPC, ADB (уже `PublishSingleFile` + `SelfContained`)
- **GUI** — Python + PyQt6, запускает бэкенд как subprocess
- **Android** — отдельный APK, не в «один бинарь» для ПК

Ниже варианты от простого к сложному.

---

## 1. Одна папка (рекомендуемый минимум)

**Идея:** Один лаунчер (exe/бинарь), рядом лежит бинарь бэкенда. Пользователь запускает только лаунчер — он сам поднимает бэкенд и открывает окно.

**Как:**
1. Собрать Backend под нужную ОС:  
   `dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true`  
   (аналогично `linux-x64`, `osx-x64`).
2. Положить бинарь в `unified/backend/` (например `MirrorSync.Backend` или `MirrorSync.Backend.exe`).
3. Собрать GUI:  
   `pyinstaller unified/MirrorSyncController.spec`  
   (или через `uv run pyinstaller`).
4. В результате папка `dist/MirrorSyncController/`: внутри лаунчер + бэкенд-бинарь + Python runtime. Всё распространять одной папкой (или zip).

**Плюсы:** уже поддерживается твоим `main.py` (поиск бэкенда в `base_path/backend/`), минимум изменений.  
**Минусы:** это папка с файлами, а не «один файл».

---

## 2. Один exe (лаунчер с вшитым бэкендом)

**Идея:** Один exe при запуске распаковывает бэкенд во временную папку (`_MEIPASS` у PyInstaller), запускает его и открывает GUI. Для пользователя — «один файл».

**Как:**
1. Собрать Backend в single-file под целевую ОС.
2. В `MirrorSyncController.spec` добавить бэкенд в `binaries`, чтобы он оказался в `backend/` внутри бандла:
   ```python
   binaries=[
       ('../path/to/MirrorSync.Backend', 'backend'),   # Linux
       # или ('../path/to/MirrorSync.Backend.exe', 'backend') для Windows
   ],
   ```
3. Собирать PyInstaller в режиме **onefile** (`--onefile`), чтобы получился один exe.
4. В `main.py` уже используется `base_path = sys._MEIPASS` при `frozen` — путь `base_path / "backend" / "MirrorSync.Backend"` будет указывать на распакованный бэкенд.

**Плюсы:** один exe, удобно раздавать.  
**Минусы:** первый запуск дольше (распаковка), под каждую ОС нужна своя сборка (win/linux/mac) и свой бинарь бэкенда в spec.

---

## 3. C#-only: один exe без Python

**Идея:** Всё в одном процессе на .NET: gRPC-сервер + Avalonia GUI. Один бинарь без Python и без subprocess.

**Как:**
- Доработать/использовать `MirrorSync.GUI` (Avalonia): при старте поднимать Kestrel/gRPC в том же процессе (в фоне), окно подключается к `localhost:50051`.
- Сборка:  
  `dotnet publish src/MirrorSync.GUI/ -c Release -r win-x64 -p:PublishSingleFile=true --self-contained true`  
  и аналогично для linux-x64 / osx-x64.

**Плюсы:** один exe, одна платформа (.NET), нет Python.  
**Минусы:** нужно довести Avalonia-GUI до уровня PyQt (списки устройств, скриншоты, тапы и т.д.).

---

## 4. Установщик (один установщик → одна папка)

**Идея:** Пользователь ставит «одну программу» через установщик; внутри — та же схема «лаунчер + бэкенд в одной папке».

**Как:**
- **Windows:** Inno Setup / NSIS: в пакет положить `dist/MirrorSyncController/` (лаунчер + бэкенд + зависимости), ярлык на лаунчер.
- **Linux:** .deb / .rpm / AppImage: в пакет те же файлы, скрипт запуска — лаунчер.
- **macOS:** .app bundle: внутри лаунчер + бэкенд, Info.plist и т.д.

**Плюсы:** привычный «установил и запустил», одна точка входа.  
**Минусы:** нужен скрипт/конфиг под каждый тип установщика.

---

## 5. Краткая рекомендация

- **Быстро и надёжно:** вариант **1 (одна папка)** + zip или простой установщик. Сборка: бэкенд → положить в `unified/backend/` → PyInstaller → раздавать папку `dist/MirrorSyncController/`.
- **Нужен именно один exe:** вариант **2 (onefile + вшитый бэкенд)**. Важно: под Windows в spec класть `MirrorSync.Backend.exe`, под Linux — `MirrorSync.Backend` без расширения, и собирать отдельный exe под каждую ОС.
- **Долгосрочно без Python:** вариант **3**, если готов вкладываться в C#/Avalonia GUI.

Дальше можно оформить один общий скрипт сборки (bash/powershell), который по параметру (win/linux/mac, onefile или onedir) собирает бэкенд и PyInstaller и при необходимости подставляет нужный бинарь бэкенда в spec.

---

## Установка агента на телефон из приложения

В программе есть кнопка **«Install Agent on device»**: по выбранному в списке устройству вызывается `adb install -r agent.apk`. Пользователь подключает телефон по USB с включённой отладкой, выбирает устройство и нажимает кнопку — агент ставится без ручной установки APK.

**Что сделано:**
- gRPC: `InstallAgent(InstallAgentRequest)` → `InstallAgentResponse`.
- Backend: ищет `agent.apk` рядом с exe (или путь из конфига `MirrorSync:AgentApkPath`), запускает `adb -s SERIAL install -r <path>`.
- GUI: кнопка «Install Agent on device», выбор устройства в таблице.

**Для установщика:**
1. Собрать APK агента (Android Studio / `./gradlew assembleRelease`) и взять `android/app/build/outputs/apk/release/...apk` (или debug).
2. Переименовать/скопировать в `agent.apk` и положить **рядом с исполняемым файлом** (или в ту же папку, куда установщик кладёт программу).
3. В установщике (Inno Setup и т.п.) добавить файл `agent.apk` в секцию `[Files]` в ту же директорию, что и exe (или в подпапку и прописать в конфиге `AgentApkPath`).

Тогда после установки ПК-приложения пользователь: подключает телефон → видит устройство в списке → нажимает «Install Agent on device» → на телефоне появляется агент, остаётся включить Accessibility Service в настройках.
