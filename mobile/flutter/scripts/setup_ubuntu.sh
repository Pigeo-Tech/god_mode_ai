#!/usr/bin/env bash
# GOD MODE AI - Flutter setup for Ubuntu.
# Installs prerequisites (with your confirmation), generates the Android platform folder,
# and fetches packages. Run from mobile/flutter:   bash scripts/setup_ubuntu.sh
set -euo pipefail

confirm() { read -r -p "$1 [y/N] " a; [[ "$a" =~ ^[Yy]$ ]]; }

echo "==> 1/5 Base packages (git, unzip, etc.)"
if confirm "Install base apt packages via sudo?"; then
  sudo apt-get update
  sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa
fi

echo "==> 2/5 Flutter SDK"
if ! command -v flutter >/dev/null 2>&1; then
  if confirm "Flutter not found. Install via snap (sudo snap install flutter --classic)?"; then
    sudo snap install flutter --classic
  else
    echo "Install Flutter manually, then re-run. See BUILD_UBUNTU.md."; exit 1
  fi
fi
flutter --version

echo "==> 3/5 Android Studio (for SDK + emulator)"
if ! command -v android-studio >/dev/null 2>&1 && [ ! -d "$HOME/android-studio" ]; then
  if confirm "Install Android Studio via snap?"; then
    sudo snap install android-studio --classic
    echo "Open Android Studio once to finish SDK setup, then re-run this script."
  fi
fi

echo "==> 4/5 Doctor + licenses"
flutter doctor || true
if confirm "Accept Android SDK licenses now?"; then
  yes | flutter doctor --android-licenses || true
fi

echo "==> 5/5 Generate platforms + packages"
flutter create --org com.godmode --project-name god_mode_ai --platforms=android .
flutter pub get

echo
echo "Done. Start an emulator or plug in a phone, then run:"
echo "  flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # emulator"
echo "  # physical phone over USB: first 'adb reverse tcp:8000 tcp:8000', then use localhost:"
echo "  flutter run --dart-define=API_BASE_URL=http://localhost:8000"
