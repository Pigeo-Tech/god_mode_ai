#!/usr/bin/env bash
# GOD MODE AI - Flutter setup (macOS / Linux)
# Generates the Android/iOS platform folders into this existing project, then fetches packages.
set -euo pipefail

echo "==> Checking Flutter..."
flutter --version
flutter doctor

echo "==> Generating platform scaffolding (keeps lib/ and pubspec.yaml)..."
flutter create --org com.godmode --project-name god_mode_ai --platforms=android,ios .

echo "==> Fetching packages..."
flutter pub get

echo "==> Done. Next:"
echo "    flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator"
echo "    flutter run --dart-define=API_BASE_URL=http://localhost:8000  # iOS simulator (macOS)"
