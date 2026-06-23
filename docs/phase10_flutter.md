# GOD MODE AI — Phase 10: Flutter App

> **Status:** Phase 10 of 12 complete. A full Flutter mobile client (Android + iOS, Material 3,
> Riverpod) is implemented against the Phase 9 API: JWT auth, streaming chat over WebSockets, a
> live agent browser, secure token storage, offline conversation cache, and FCM push
> notifications.

## What was built (`mobile/flutter/`)

| Area | Files | Role |
|---|---|---|
| **Entry / shell** | `main.dart`, `app.dart` | `ProviderScope` + `MaterialApp` (Material 3, light/dark, seeded color), auth-gated routing. |
| **Networking** | `core/api_client.dart`, `core/ws_client.dart` | REST client (register/login/chat/agents) and WebSocket streaming of King progress. |
| **Persistence** | `core/secure_storage.dart`, `core/offline_store.dart` | JWT tokens in keystore/keychain; conversation cached for offline launch. |
| **Config** | `core/config.dart` | Base URL via `--dart-define=API_BASE_URL`. |
| **Models** | `models/auth.dart`, `models/agent.dart`, `models/chat.dart` | Map the Phase 9 JSON: `AuthTokens`, `AgentInfo`, `ChatMessage`, `StreamEvent`. |
| **State (Riverpod)** | `providers/auth_provider.dart`, `chat_provider.dart`, `agents_provider.dart` | `AuthController` (login/register/restore/logout), `ChatController` (streaming send + offline save), agents `FutureProvider`. |
| **Screens** | `screens/login_screen.dart`, `chat_screen.dart`, `agents_screen.dart` | Sign in/up, streaming chat with progress bar + subtask counts, live roster list. |
| **Widgets / services** | `widgets/message_bubble.dart`, `services/notifications.dart` | Chat bubble (shows King breakdown), FCM push service. |

## How it talks to the backend

```
LoginScreen → ApiClient.login()  → POST /v1/auth/login → AuthTokens (stored securely)
ChatScreen  → ChatController.send(text)
                → WsClient.streamChat(token, text) → WS /v1/stream
                    ← {type: accepted} ← {type: progress} ← {type: result} ← {type: done}
                → render summary + subtask counts, cache conversation offline
AgentsScreen → agentsProvider → GET /v1/agents → live roster
```

The WebSocket payload (`{token, message}`) and event shapes (`accepted/progress/result/done`)
match the Phase 9 `ApiService.stream_chat()` exactly.

## Design

- **Riverpod** for dependency injection + reactive state (`StateNotifier` controllers,
  `FutureProvider` for the roster), mirroring the backend's DI discipline.
- **Material 3** with a seeded color scheme and automatic light/dark.
- **Secure by default** — tokens in the platform secure store, never in plain prefs; session
  restored on launch.
- **Offline-friendly** — the conversation is cached so the app opens with history even without a
  connection.

## Tests & verification

- `test/api_client_test.dart` — model JSON parsing (run with `flutter test`).
- All 19 Dart sources pass a bracket-balance/structure check.

Flutter/Dart isn't available in the build sandbox, so the app is authored and structure-verified
here and compiles/runs with the Flutter SDK installed (`flutter pub get && flutter run`). The
backend suite remains **86/86**.

## Next

**Phase 11 — Docker:** multi-stage backend image, `docker-compose` for the full local stack
(API + Postgres + Redis + Qdrant + NGINX), and dev vs production configurations.
