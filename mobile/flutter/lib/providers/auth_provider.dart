import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api_client.dart';
import '../core/secure_storage.dart';
import '../models/auth.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final tokenStoreProvider = Provider<SecureTokenStore>((ref) => SecureTokenStore());

class AuthState {
  final AuthTokens? tokens;
  final bool loading;
  final String? error;
  const AuthState({this.tokens, this.loading = false, this.error});

  bool get isAuthenticated => tokens != null;

  AuthState copyWith({AuthTokens? tokens, bool? loading, String? error}) =>
      AuthState(
        tokens: tokens ?? this.tokens,
        loading: loading ?? this.loading,
        error: error,
      );
}

class AuthController extends StateNotifier<AuthState> {
  final ApiClient _api;
  final SecureTokenStore _store;

  AuthController(this._api, this._store) : super(const AuthState()) {
    // Persist any silently-refreshed access token so the session never visibly expires.
    _api.onTokens = (t) {
      final merged = AuthTokens(
        accessToken: t.accessToken,
        refreshToken: t.refreshToken ?? state.tokens?.refreshToken,
        userId: state.tokens?.userId ?? '',
      );
      _store.save(merged);
      state = state.copyWith(tokens: merged);
    };
  }

  Future<void> restore() async {
    final saved = await _store.read();
    if (saved != null) {
      _api.setTokens(saved);
      state = state.copyWith(tokens: saved);
    }
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(loading: true, error: null);
    try {
      final tokens = await _api.login(email, password);
      await _store.save(tokens);
      state = AuthState(tokens: tokens);
    } catch (e) {
      state = AuthState(error: e.toString());
    }
  }

  Future<void> register(String email, String password) async {
    state = state.copyWith(loading: true, error: null);
    try {
      await _api.register(email, password);
      await login(email, password);
    } catch (e) {
      state = AuthState(error: e.toString());
    }
  }

  Future<void> logout() async {
    await _store.clear();
    _api.setToken(null);
    state = const AuthState();
  }
}

final authProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref.watch(apiClientProvider), ref.watch(tokenStoreProvider));
});
