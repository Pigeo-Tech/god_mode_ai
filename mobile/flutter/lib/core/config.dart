/// App configuration. Override [baseUrl] per environment at build time with
/// `--dart-define=API_BASE_URL=https://api.godmode.ai`.
class AppConfig {
  static const String baseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');

  static String get wsUrl =>
      baseUrl.replaceFirst('http', 'ws') + '/v1/stream';
}
