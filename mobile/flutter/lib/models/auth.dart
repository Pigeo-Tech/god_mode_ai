/// Tokens returned by POST /v1/auth/login.
class AuthTokens {
  final String accessToken;
  final String? refreshToken;
  final String userId;

  const AuthTokens({
    required this.accessToken,
    required this.userId,
    this.refreshToken,
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String?,
        userId: (json['user_id'] ?? '') as String,
      );

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'user_id': userId,
      };
}
