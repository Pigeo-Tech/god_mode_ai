# AGNI — Ubuntu Runbook (backend → Flutter → build & install the app)

One sequence, copy-paste friendly. Do the parts in order. Everything here is **₹0** (local dev).

> Your project lives at `/mnt/d/Agni Advance/god_mode_ai`. The space in "Agni Advance" means you
> must **quote the path every time**:  `cd "/mnt/d/Agni Advance/god_mode_ai"`.
> If you're on WSL (your prompt shows `/mnt/d`), read the **WSL note** boxes.

---

## PART A — Run the backend (Terminal #1)

```bash
cd "/mnt/d/Agni Advance/god_mode_ai"
bash scripts/dev.sh
```

That script makes a virtualenv, installs dependencies, and starts the API with the full
161-agent system in memory. Leave it running. You should see:

```
==> API on http://localhost:8000  (docs at /docs).
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Verify** (Terminal #2):
```bash
curl http://localhost:8000/health        # -> {"status":"ok","phase":...}
```
Open `http://localhost:8000/docs` in a browser to see all the API endpoints.

> **WSL note:** `localhost` works from Windows too (WSL2 forwards it). For a **phone** to reach it
> later, see PART D's WSL networking box.

If `python3 -m venv` complains, install it once:
```bash
sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
```

---

## PART B — Install Flutter + Android tooling (one time, Terminal #2)

```bash
sudo apt-get update
sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa
sudo snap install flutter --classic
flutter --version          # first run downloads the engine (takes a minute)
```

Install the Android SDK (needed to build an APK). Easiest is Android Studio:
```bash
sudo snap install android-studio --classic
```
Open **Android Studio** once → let the wizard install the **Android SDK** + **command-line
tools** + a **system image**. Then accept licenses:
```bash
flutter doctor --android-licenses     # press y through all
flutter doctor                        # want green ticks for Flutter + Android toolchain
```

---

## PART C — Generate the project + build the app (Terminal #2)

```bash
cd "/mnt/d/Agni Advance/god_mode_ai/mobile/flutter"
bash scripts/setup_ubuntu.sh          # generates android/, runs flutter pub get
```

Build a release APK (point it at your machine's address — see which to use below):
```bash
flutter build apk --release --dart-define=API_BASE_URL=http://10.0.2.2:8000
# output: build/app/outputs/flutter-apk/app-release.apk
```

- Use `http://10.0.2.2:8000` if you'll run it on the **Android emulator**.
- Use `http://<YOUR-PC-LAN-IP>:8000` if you'll install on a **physical phone** (find it with
  `hostname -I` on native Ubuntu, or see the WSL box in PART D).

---

## PART D — Run it (pick ONE)

### Option 1 — Android emulator (native Ubuntu, simplest)
```bash
flutter emulators                       # list; create one in Android Studio if empty
flutter emulators --launch <emulator_id>
cd "/mnt/d/Agni Advance/god_mode_ai/mobile/flutter"
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```
Register an account on the login screen, type *"research quantum computing"*, watch the King work.

> **WSL note:** running the Android emulator inside WSL is unreliable. On WSL, prefer **Option 2
> (physical phone)** or **Option 3 (web)**.

### Option 2 — Physical Android phone (install the APK you built)
1. Copy `build/app/outputs/flutter-apk/app-release.apk` to your phone (USB, Google Drive, or
   `cp` it to `/mnt/c/Users/<you>/Desktop/` and transfer from Windows).
2. On the phone: Settings → allow "Install unknown apps" for your file manager, then tap the APK.
3. The phone must reach your backend. On the **same Wi-Fi**, use your PC's LAN IP as
   `API_BASE_URL` (rebuild the APK with it if needed).

> **WSL networking (phone → backend):** WSL2 has its own internal IP, so a phone can't hit it
> directly. On **Windows PowerShell (as Admin)** run:
> ```powershell
> $wsl = (wsl hostname -I).Trim().Split(" ")[0]
> netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wsl
> New-NetFirewallRule -DisplayName "AGNI 8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
> ```
> Then build the APK with `API_BASE_URL=http://<YOUR-WINDOWS-LAN-IP>:8000` (find it with
> `ipconfig`). The phone now reaches Windows → forwarded to WSL.

### Option 3 — Web browser (fastest test, no Android needed) ✅ great on WSL
```bash
cd "/mnt/d/Agni Advance/god_mode_ai/mobile/flutter"
flutter config --enable-web
flutter create --platforms=web .
flutter run -d web-server --web-port 9000 --dart-define=API_BASE_URL=http://localhost:8000
# open http://localhost:9000
```
This runs the exact same app in a browser — no emulator, no SDK licenses, no phone. Best way to
develop the UI quickly while the backend runs in Terminal #1.

---

## The whole thing in order (cheat sheet)

```bash
# Terminal 1 — backend
cd "/mnt/d/Agni Advance/god_mode_ai" && bash scripts/dev.sh

# Terminal 2 — one-time setup
sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa
sudo snap install flutter --classic
sudo snap install android-studio --classic        # open once to install the SDK
flutter doctor --android-licenses

# Terminal 2 — build the app
cd "/mnt/d/Agni Advance/god_mode_ai/mobile/flutter"
bash scripts/setup_ubuntu.sh
flutter build apk --release --dart-define=API_BASE_URL=http://10.0.2.2:8000
# OR, fastest on WSL, test in a browser:
flutter config --enable-web && flutter create --platforms=web .
flutter run -d web-server --web-port 9000 --dart-define=API_BASE_URL=http://localhost:8000
```

---

## Common errors

| Error | Fix |
|---|---|
| `cd: too many arguments` | Quote the path: `cd "/mnt/d/Agni Advance/god_mode_ai"`. |
| bash shows `>` and waits | An unclosed `"`. Press `Ctrl-C` and retype with matching quotes. |
| `python3-venv` missing | `sudo apt-get install -y python3-venv python3-pip`. |
| `flutter: not found` after snap | Close and reopen the terminal (PATH refresh). |
| Android licenses not accepted | `flutter doctor --android-licenses`, press `y` to all. |
| App "connection refused" | Wrong `API_BASE_URL`. Emulator → `10.0.2.2`; phone → PC LAN IP (+ WSL portproxy). Check `curl http://localhost:8000/health` works first. |
| Emulator won't start in WSL | Use Option 2 (phone) or Option 3 (web). |
| Gradle/Firebase build error | Comment out `firebase_messaging` in `pubspec.yaml` for the first build (push is optional). |
```
