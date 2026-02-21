#!/bin/bash
echo "=== Тестирование Backend ==="
cd /home/foxi/Project/MirrorSyncController/src/MirrorSync.Backend
dotnet run --no-build -c Release &
BACKEND_PID=$!
sleep 3
echo "Backend запущен с PID: $BACKEND_PID"
kill $BACKEND_PID
echo "Backend остановлен"
