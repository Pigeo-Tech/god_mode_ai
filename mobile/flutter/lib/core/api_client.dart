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

  ApiClient([http.Client? client]) : _http = client ?? http.Client();

  void setToken(String? token) => _accessToken = token;

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
    setToken(tokens.accessToken);
    return tokens;
  }

  /// Non-streaming chat (single response).
  Future<Map<String, dynamic>> chat(String message) async {
    final r = await _http.post(_uri('/v1/chat'),
        headers: _headers, body: jsonEncode({'message': message, 'stream': false}));
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
    final r = await _http.get(_uri('/v1/agents'), headers: _headers);
    final json = await _decode(r) as Map<String, dynamic>;
    final list = (json['agents'] as List<dynamic>);
    return list.map((e) => AgentInfo.fromJson(e as Map<String, dynamic>)).toList();
  }
}
