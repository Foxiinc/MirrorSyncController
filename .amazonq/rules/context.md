CONTEXT:
Проект: MirrorSyncController.
Цель: синхронное управление 2–20 Android-устройствами с Windows-ПК (USB/ADB сначала), зеркалирование экранов и выполнение жестов (tap/swipe/text/key) с суб-10 ms синхронностью между устройствами.
Технологии: Backend — .NET 8 (C#), GUI — Python 3.11 + PyQt6, Agent — Android (Kotlin, AccessibilityService), GUI↔Backend — gRPC, Backend↔Agent — TCP (JSON или protobuf).
Платформа сборки: Windows 10/11 x64. Installer: Inno Setup.
Требования: точность, нормализация координат (0..1), adb port-forward, scrcpy для зеркалирования, инсталлятор.