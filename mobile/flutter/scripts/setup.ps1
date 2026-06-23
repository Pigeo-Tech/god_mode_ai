# GOD MODE AI - Flutter setup (Windows / PowerShell)
# Generates the Android/iOS platform folders into this existing project, then fetches packages.
# Run from mobile/flutter:   ./scripts/setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "==> Checking Flutter..." -ForegroundColor Cyan
flutter --version
flutter doctor

Write-Host "==> Generating platform scaffolding (keeps lib/ and pubspec.yaml)..." -ForegroundColor Cyan
# --org sets the bundle id prefix (com.godmode.god_mode_ai); add web/windows if you want them.
flutter create --org com.godmode --project-name god_mode_ai --platforms=android,ios .

Write-Host "==> Fetching packages..." -ForegroundColor Cyan
flutter pub get

Write-Host "==> Done. Next:" -ForegroundColor Green
Write-Host "    flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000"
