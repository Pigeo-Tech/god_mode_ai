import 'package:shared_preferences/shared_preferences.dart';

/// Runtime-configurable backend URL. Defaults to the --dart-define value, but can be
/// overridden in-app (Server URL field) and is persisted across launches.
class ServerConfig {
  static const _key = 'server_base_url';
  static String _baseUrl = const String.fromEnvironment(
      'API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');

  static String get baseUrl => _baseUrl;
  static String get wsUrl => _baseUrl.replaceFirst('http', 'ws') + '/v1/stream';

  static Future<void> load() async {
    final p = await SharedPreferences.getInstance();
    final saved = p.getString(_key);
    if (saved != null && saved.isNotEmpty) _baseUrl = saved;
  }

  static Future<void> set(String url) async {
    url = url.trim();
    while (url.endsWith('/')) {
      url = url.substring(0, url.length - 1);
    }
    if (url.isEmpty) return;
    _baseUrl = url;
    final p = await SharedPreferences.getInstance();
    await p.setString(_key, url);
  }
}
