#!/usr/bin/env bash
# Re-apply Buddy's AndroidManifest after `flutter create .` regenerates it.
# Adds the permissions (internet, mic, foreground-service) and the audio-playback service that
# the in-app music player + background/lock-screen controls require, and names the app "Buddy".
#
# Run from the flutter project root, AFTER `flutter create .`:
#   bash setup_android.sh
set -e
M="android/app/src/main/AndroidManifest.xml"
[ -f "$M" ] || { echo "Run this from the flutter project root (no $M found)"; exit 1; }

# 1) Permissions — add each one only if it's missing
add_perm() {
  grep -q "$1" "$M" || sed -i \
    "s#<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">#<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">\n    <uses-permission android:name=\"$1\"/>#" \
    "$M"
}
add_perm "android.permission.INTERNET"
add_perm "android.permission.RECORD_AUDIO"
add_perm "android.permission.FOREGROUND_SERVICE"
add_perm "android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK"
add_perm "android.permission.WAKE_LOCK"

# 2) Audio service + media-button receiver (required by just_audio_background)
grep -q "com.ryanheise.audioservice.AudioService" "$M" || sed -i \
  's#</application>#    <service android:name="com.ryanheise.audioservice.AudioService" android:foregroundServiceType="mediaPlayback" android:exported="true"><intent-filter><action android:name="android.media.browse.MediaBrowserService"/></intent-filter></service>\n        <receiver android:name="com.ryanheise.audioservice.MediaButtonReceiver" android:exported="true"><intent-filter><action android:name="android.intent.action.MEDIA_BUTTON"/></intent-filter></receiver>\n    </application>#' \
  "$M"

# 3) App name
sed -i 's#android:label="god_mode_ai"#android:label="Buddy"#' "$M"

echo "AndroidManifest patched. Permissions + audio service added."
grep -E "uses-permission|AudioService|android:label" "$M"
