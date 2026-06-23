import 'package:firebase_messaging/firebase_messaging.dart';

/// Push notifications via Firebase Cloud Messaging.
///
/// Call [init] after sign-in; [register] the returned FCM token with the backend
/// so the platform can notify the user when a long-running King request completes.
class NotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  Future<String?> init() async {
    final settings = await _fcm.requestPermission(alert: true, badge: true, sound: true);
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      return null;
    }
    FirebaseMessaging.onMessage.listen(_onForegroundMessage);
    return _fcm.getToken();
  }

  void _onForegroundMessage(RemoteMessage message) {
    // A local-notification plugin would surface this in the tray; logged for now.
    final title = message.notification?.title ?? 'GOD MODE AI';
    final body = message.notification?.body ?? '';
    // ignore: avoid_print
    print('push: $title — $body');
  }
}
