import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/agent.dart';
import '../models/auth.dart';
import 'server_config.dart';

class ApiException implements Exception {
  final int status;
  final String message;
  ApiException(this.status, this.message);
  @override
  String toString() => 'ApiException($status): $message';
}

/// Thin REST client over the Phase 9 API.
class ApiClient {
  final http.Client _http;
  String? _accessToken;
  String? _refreshToken;

  /// Called when a refreshed access token is obtained, so it can be persisted.
  void Function(AuthTokens tokens)? onTokens;

  ApiClient([http.Client? client]) : _http = client ?? http.Client();

  void setToken(String? token) => _accessToken = token;

  /// Set both tokens (so the client can silently refresh an expired access token).
  void setTokens(AuthTokens t) {
    _accessToken = t.accessToken;
    _refreshToken = t.refreshToken;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Uri _uri(String path) => Uri.parse('${ServerConfig.baseUrl}$path');

  Future<dynamic> _decode(http.Response r) async {
    final body = r.body.isEmpty ? null : jsonDecode(r.body);
    if (r.statusCode >= 400) {
      final detail = body is Map ? body['detail']?.toString() : r.body;
      throw ApiException(r.statusCode, detail ?? 'request failed');
    }
    return body;
  }

  /// Use the refresh token to get a new access token. Returns true on success.
  Future<bool> _refresh() async {
    if (_refreshToken == null) return false;
    try {
      final r = await _http.post(_uri('/v1/auth/refresh'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh_token': _refreshToken}));
      if (r.statusCode != 200) return false;
      final j = jsonDecode(r.body) as Map<String, dynamic>;
      _accessToken = j['access_token'] as String;
      onTokens?.call(AuthTokens(
          accessToken: _accessToken!, refreshToken: _refreshToken, userId: ''));
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Run an authed request; if the token has expired (401), refresh once and retry.
  Future<http.Response> _send(Future<http.Response> Function() build) async {
    var r = await build();
    if (r.statusCode == 401 && await _refresh()) {
      r = await build();
    }
    return r;
  }

  Future<void> register(String email, String password) async {
    final r = await _http.post(_uri('/v1/auth/register'),
        headers: _headers, body: jsonEncode({'email': email, 'password': password}));
    await _decode(r);
  }

  Future<AuthTokens> login(String email, String password) async {
    final r = await _http.post(_uri('/v1/auth/login'),
        headers: _headers, body: jsonEncode({'email': email, 'password': password}));
    final json = await _decode(r) as Map<String, dynamic>;
    final tokens = AuthTokens.fromJson(json);
    setTokens(tokens);
    return tokens;
  }

  /// Non-streaming chat (single response). Auto-refreshes the token on expiry.
  Future<Map<String, dynamic>> chat(String message) async {
    final r = await _send(() => _http.post(_uri('/v1/chat'),
        headers: _headers, body: jsonEncode({'message': message, 'stream': false})));
    return await _decode(r) as Map<String, dynamic>;
  }

  /// Ask the backend to synthesize speech (ElevenLabs) for [text]. Returns MP3 bytes, or null
  /// if voice isn't configured / the request failed (caller falls back to device TTS).
  Future<List<int>?> tts(String text) async {
    try {
      final r = await _http.post(_uri('/v1/tts'),
          headers: _headers, body: jsonEncode({'text': text}));
      if (r.statusCode == 200 && r.bodyBytes.isNotEmpty) return r.bodyBytes;
    } catch (_) {/* fall through to device TTS */}
    return null;
  }

  Future<List<AgentInfo>> agents() async {
    final r = await _send(() => _http.get(_uri('/v1/agents'), headers: _headers));
    final json = await _decode(r) as Map<String, dynamic>;
    final list = (json['agents'] as List<dynamic>);
    return list.map((e) => AgentInfo.fromJson(e as Map<String, dynamic>)).toList();
  }
}
