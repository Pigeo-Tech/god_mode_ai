# Building & Running the GOD MODE AI App

This guide takes you from a fresh machine to the app running on a phone, talking to your backend.
The repo ships the app **source** (`lib/`, `pubspec.yaml`, tests) but not the generated
Android/iOS platform folders — those are created by `flutter create` in Step 3.

You are on Windows, so commands below are **PowerShell-first**; macOS/Linux equivalents are noted.
(iOS builds require a Mac with Xcode — Android works on Windows.)

---

## 0. What you'll end up with

```
You run the backend  →  http://localhost:8000   (REST + WebSocket)
You run the app      →  Android emulator/phone   →  talks to backend
```

---

## 1. Install the toolchain (one time)

1. **Flutter SDK** — install via the official instructions for Windows, then add `flutter\bin`
   to your PATH. Verify:
   ```powershell
   flutter --version
   ```
2. **Android Studio** — install it, then open *More Actions → SDK Manager* and ensure
   **Android SDK**, **Android SDK Command-line Tools**, and an **emulator image** are installed.
   Also install the **Flutter** and **Dart** plugins (Settings → Plugins).
3. Run the doctor and fix anything it flags (accept Android licenses when asked):
   ```powershell
   flutter doctor
   flutter doctor --android-licenses
   ```

When `flutter doctor` shows a check next to "Flutter" and "Android toolchain", you're ready.

---

## 2. Start the backend

The app needs the Phase 9 API running. Easiest is Docker (from the repo root `god_mode_ai/`):

```powershell
docker compose -f docker/docker-compose.yml up --build
```

Or run it directly with Python:

```powershell
cd god_mode_ai
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

Confirm it's up: open <http://localhost:8000/health> (should return `{"status":"ok",...}`) and
<http://localhost:8000/docs> for the API explorer.

> **Networking note.** The Android **emulator** reaches your PC at `10.0.2.2`, not `localhost`.
> A physical Android **phone** must use your PC's LAN IP (e.g. `192.168.1.50`) and be on the
> same Wi-Fi. iOS simulator uses `localhost`.

---

## 3. Generate the platform folders + packages

From `mobile/flutter/`, run the setup script (creates `android/`, `ios/`, fetches packages —
your `lib/` and `pubspec.yaml` are preserved):

```powershell
cd mobile\flutter
./scripts/setup.ps1
```

macOS/Linux: `./scripts/setup.sh`. Or do it manually:

```powershell
flutter create --org com.godmode --project-name god_mode_ai --platforms=android,ios .
flutter pub get
```

---

## 4. Run on an emulator (debug)

1. Launch an emulator: Android Studio → *Device Manager* → ▶ on a virtual device
   (or `flutter emulators --launch <id>`).
2. From `mobile/flutter/`:
   ```powershell
   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
   ```
3. The app opens on the **Login** screen. Tap **Create an account**, register, and you're in.
   Type an objective like *"research the market and check the stock price then notify me"* —
   you'll see the King's live progress and the aggregated answer.

Hot-reload: press `r` in the terminal after editing Dart; `R` for a full restart; `q` to quit.

**Physical Android phone:** enable Developer Options + USB debugging, plug in, then:
```powershell
flutter devices                      # confirm it's listed
flutter run --dart-define=API_BASE_URL=http://<YOUR-PC-LAN-IP>:8000
```

---

## 5. Run the tests (optional)

```powershell
flutter test
```

This runs `test/api_client_test.dart` (model parsing).

---

## 6. Build a release

**Android APK** (sideloadable single file):
```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://your-api.example.com
# output: build\app\outputs\flutter-apk\app-release.apk
```

**Android App Bundle** (for the Play Store):
```powershell
flutter build appbundle --release --dart-define=API_BASE_URL=https://your-api.example.com
# output: build\app\outputs\bundle\release\app-release.aab
```

> Release builds for the Play Store must be **signed**. Create a keystore and a
> `android/key.properties`, and reference it in `android/app/build.gradle` — follow Flutter's
> "Build and release an Android app" page. For local testing the unsigned debug build is fine.

**iOS** (requires macOS + Xcode):
```bash
flutter build ipa --release --dart-define=API_BASE_URL=https://your-api.example.com
```
Then upload with Xcode/Transporter. Signing needs an Apple Developer account.

> Tip: instead of passing `--dart-define` every time, you can put it in a
> `--dart-define-from-file=env.json` file, or define `API_BASE_URL` per build flavor.

---

## 7. Push notifications (optional — Firebase)

The app includes `firebase_messaging`, but push is **opt-in** and not called on startup, so the
app builds and runs without any Firebase setup. To enable real push later:

1. Install the FlutterFire CLI and configure the project:
   ```powershell
   dart pub global activate flutterfire_cli
   flutterfire configure
   ```
   This creates `firebase_options.dart` and the platform config
   (`google-services.json` / `GoogleService-Info.plist`).
2. Initialize Firebase in `main.dart` and call `NotificationService().init()` after sign-in;
   send the returned FCM token to your backend.

If you hit an Android Gradle error about Firebase before configuring it, comment out the
`firebase_messaging` line in `pubspec.yaml` (and the import in `lib/services/notifications.dart`)
for your first build, then add it back when you set up Firebase.

---

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| App loads but login fails / "connection refused" | Backend not reachable. On the **emulator** use `10.0.2.2`, on a **phone** use the PC's LAN IP; confirm `/health` works in a browser. |
| `flutter: command not found` | `flutter\bin` isn't on PATH — reopen the terminal after adding it. |
| Android licenses not accepted | `flutter doctor --android-licenses` and accept all. |
| Gradle/Firebase build error | See Step 7 — temporarily remove `firebase_messaging` for the first build. |
| Stale build after edits | `flutter clean ; flutter pub get` then run again. |
| Can't reach backend over HTTPS with a self-signed cert | Use a real cert, or test over plain HTTP on localhost/LAN. |

---

## Quick reference

```powershell
# one-time
./scripts/setup.ps1

# everyday (emulator)
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# release APK
flutter build apk --release --dart-define=API_BASE_URL=https://your-api.example.com
```
