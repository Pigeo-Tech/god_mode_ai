# GOD MODE AI — Flutter App (Phase 10)

Android + iOS client for the GOD MODE AI platform. Material 3, Riverpod state, REST +
WebSocket streaming against the Phase 9 API, secure JWT storage, offline conversation cache,
and FCM push notifications.

## Structure
```
lib/
├── main.dart                 ProviderScope entrypoint
├── app.dart                  MaterialApp (Material 3, light/dark), auth-gated routing
├── core/
│   ├── config.dart           base URL (--dart-define=API_BASE_URL=...)
│   ├── api_client.dart       REST client (auth, chat, agents)
│   ├── ws_client.dart        WebSocket streaming (/v1/stream)
│   ├── secure_storage.dart   JWT tokens in keystore/keychain
│   └── offline_store.dart    conversation cache (shared_preferences)
├── models/                   AuthTokens, AgentInfo, ChatMessage, StreamEvent
├── providers/                Riverpod: auth, chat, agents
├── screens/                  login, chat (streaming), agents roster
├── widgets/                  message bubble
└── services/notifications.dart   FCM push
```

## Run
```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # Android emulator -> host
```
`10.0.2.2` reaches the host machine from the Android emulator; use your LAN IP for a device.

## Flow
Login/Register → JWT stored securely → Chat screen sends an objective over the WebSocket and
renders live King progress (accepted → progress → result) → conversation cached offline. The
Agents screen lists the live roster from `GET /v1/agents`.

## Tests
`test/api_client_test.dart` covers model JSON parsing. Run with `flutter test` (requires the
Flutter SDK, not available in the build sandbox where this was authored).
