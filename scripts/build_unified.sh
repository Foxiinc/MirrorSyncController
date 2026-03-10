#!/usr/bin/env bash
# Сборка MirrorSync Controller: Backend + GUI в одну папку (onedir).
# Запуск из корня репозитория: ./scripts/build_unified.sh [win|linux|mac]

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Целевая ОС: по умолчанию текущая
case "${1:-}" in
  win)   RID="win-x64";     BACKEND_NAME="MirrorSync.Backend.exe";;
  mac)   RID="osx-x64";     BACKEND_NAME="MirrorSync.Backend";;
  *)     RID="linux-x64";   BACKEND_NAME="MirrorSync.Backend";;
esac

echo "=== 1. Backend (${RID}) ==="
dotnet publish src/MirrorSync.Backend/MirrorSync.Backend.csproj \
  -c Release -r "$RID" --self-contained true \
  -p:PublishSingleFile=true -o "$ROOT/unified/backend"

# Имя бинаря может отличаться на Windows
if [[ "$RID" == win-* ]] && [[ ! -f "$ROOT/unified/backend/MirrorSync.Backend.exe" ]]; then
  BACKEND_NAME="MirrorSync.Backend.exe"
fi
echo "Backend -> unified/backend/${BACKEND_NAME}"

echo "=== 2. GUI (PyInstaller onedir) ==="
cd unified
# Убедиться, что backend на месте
if [[ ! -f "backend/$BACKEND_NAME" ]]; then
  echo "Error: backend binary not found at backend/$BACKEND_NAME"
  exit 1
fi

# Зависимости: PyQt6 + grpcio (в pyproject указан PyQt5 — для сборки лучше явно PyQt6)
uv pip install PyQt6 grpcio grpcio-tools protobuf pyinstaller 2>/dev/null || pip install PyQt6 grpcio grpcio-tools protobuf pyinstaller

pyinstaller --noconfirm MirrorSyncController.spec

echo "=== Done ==="
echo "Output: unified/dist/MirrorSyncController/"
echo "Run: unified/dist/MirrorSyncController/MirrorSyncController (or .exe on Windows)"
