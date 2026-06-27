import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio_background/just_audio_background.dart';

import 'app.dart';
import 'core/server_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ServerConfig.load();
  // Background music + lock-screen / notification controls for Buddy's in-app player.
  await JustAudioBackground.init(
    androidNotificationChannelId: 'com.agni.buddy.audio',
    androidNotificationChannelName: 'Buddy Playback',
    androidNotificationOngoing: true,
  );
  runApp(const ProviderScope(child: GodModeApp()));
}
