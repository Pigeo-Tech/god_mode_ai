# Building & Running the GOD MODE AI App on Ubuntu

Ubuntu builds the **Android** app fully (and Linux-desktop if you want). iOS requires macOS, so
that's out of scope here. The repo ships the app **source** (`lib/`, `pubspec.yaml`, tests) but
not the generated `android/` folder — `flutter create` produces it in Step 3.

There's a helper script that automates Steps 1–3: `bash scripts/setup_ubuntu.sh`. The manual
steps are below so you know what it does.

---

## 0. The shape of it

```
Backend runs on your Ubuntu box  →  http://localhost:8000
Android emulator/phone           →  reaches it (10.0.2.2 on emulator, adb reverse on USB)
```

---

## 1. Install Flutter + build deps

```bash
sudo apt-get update
sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa

# Easiest Flutter install on Ubuntu:
sudo snap install flutter --classic
flutter --version          # first run downloads the engine; give it a minute
```

(Prefer no snap? Download the Flutter Linux tarball, extract to `~/flutter`, and add
`export PATH="$HOME/flutter/bin:$PATH"` to `~/.bashrc`.)

If you also want to run/test it as a **Linux desktop** app, add:
```bash
sudo apt-get install -y clang cmake ninja-build pkg-config libgtk-3-dev
```

---

## 2. Android tooling (SDK + emulator)

```bash
sudo snap install android-studio --classic
```
Launch **Android Studio** once and let the setup wizard install the **Android SDK**,
**command-line tools**, and a **system image**. Then in *More Actions → Virtual Device Manager*
create an emulator (e.g. Pixel 7, API 34).

Accept the SDK licenses and verify the toolchain:
```bash
flutter doctor --android-licenses     # press y through them
flutter doctor                        # want green checks for Flutter + Android toolchain
```

**Faster emulator (optional but recommended):** enable hardware acceleration (KVM):
```bash
sudo apt-get install -y qemu-kvm
sudo adduser "$USER" kvm
# log out/in (or: newgrp kvm) so the group membership applies
```

---

## 3. Generate the Android project + packages

From `mobile/flutter/`:
```bash
flutter create --org com.godmode --project-name god_mode_ai --platforms=android .
flutter pub get
```
This adds `android/` (and Gradle config) while keeping your `lib/` and `pubspec.yaml`.

---

## 4. Start the backend (separate terminal)

Docker is simplest (from the repo root `god_mode_ai/`):
```bash
docker compose -f docker/docker-compose.yml up --build
```
Or with Python:
```bash
cd god_mode_ai
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```
Check it: `curl http://localhost:8000/health` → `{"status":"ok",...}`; API docs at
<http://localhost:8000/docs>.

---

## 5. Run the app

### Option A — Android emulator
Start the emulator (Android Studio Device Manager, or `flutter emulators --launch <id>`), then:
```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```
`10.0.2.2` is how the emulator reaches your host's `localhost`.

### Option B — Physical Android phone over USB
Enable **Developer options → USB debugging**, plug in, accept the RSA prompt, then:
```bash
flutter devices                       # confirm your phone is listed
adb reverse tcp:8000 tcp:8000         # forwards phone's localhost:8000 -> your PC
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```
`adb reverse` is the clean trick on Linux — the phone uses `localhost` and it tunnels to your
machine over USB (no Wi-Fi/IP juggling). If `adb` isn't on PATH, it's under
`~/Android/Sdk/platform-tools/`.

Once running: register an account on the Login screen, then type an objective like
*"research the market and check the stock price then notify me"* and watch the King stream
progress. Press `r` to hot-reload, `R` to restart, `q` to quit.

---

## 6. Tests

```bash
flutter test
```

---

## 7. Build a release APK

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://your-api.example.com
# -> build/app/outputs/flutter-apk/app-release.apk
```
App Bundle for Play Store:
```bash
flutter build appbundle --release --dart-define=API_BASE_URL=https://your-api.example.com
# -> build/app/outputs/bundle/release/app-release.aab
```
Play Store uploads must be **signed**: create a keystore with `keytool`, add
`android/key.properties`, and reference it in `android/app/build.gradle` (Flutter's
"Build and release an Android app" page has the exact snippet). The debug APK needs no signing.

---

## 8. Push notifications (optional)

`firebase_messaging` is included but only used if you call it, so the app builds without Firebase.
To enable: `dart pub global activate flutterfire_cli && flutterfire configure`, then init Firebase
in `main.dart` and call `NotificationService().init()` after sign-in. If a Gradle/Firebase error
blocks your first build, comment out `firebase_messaging` in `pubspec.yaml` (and its import in
`lib/services/notifications.dart`), build, then add it back once Firebase is configured.

---

## 9. Troubleshooting (Ubuntu)

| Symptom | Fix |
|---|---|
| Login fails / connection refused | Wrong base URL. Emulator → `10.0.2.2`; USB phone → `adb reverse` + `localhost`; confirm `curl localhost:8000/health` works. |
| `flutter doctor` flags Android licenses | `flutter doctor --android-licenses` and accept. |
| Emulator won't start / very slow | Enable KVM (Step 2); confirm with `kvm-ok` (`sudo apt install cpu-checker`). |
| `adb: command not found` | Add `~/Android/Sdk/platform-tools` to PATH. |
| Phone not detected | Check `flutter devices`; you may need a udev rule, or just re-accept the USB-debugging prompt on the phone. |
| `cmdline-tools component is missing` | Android Studio → SDK Manager → SDK Tools → install "Android SDK Command-line Tools". |
| Snap Flutter permission issues | If snap confinement bites, install Flutter via the manual tarball instead. |
| Stale build | `flutter clean && flutter pub get`, then run again. |

---

## Quick reference

```bash
# one-time
bash scripts/setup_ubuntu.sh
# everyday (emulator)
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
# everyday (USB phone)
adb reverse tcp:8000 tcp:8000
flutter run --dart-define=API_BASE_URL=http://localhost:8000
# release
flutter build apk --release --dart-define=API_BASE_URL=https://your-api.example.com
```
