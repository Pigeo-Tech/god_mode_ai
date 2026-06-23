import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/auth_provider.dart';
import 'screens/chat_screen.dart';
import 'screens/login_screen.dart';

class GodModeApp extends ConsumerStatefulWidget {
  const GodModeApp({super.key});
  @override
  ConsumerState<GodModeApp> createState() => _GodModeAppState();
}

class _GodModeAppState extends ConsumerState<GodModeApp> {
  @override
  void initState() {
    super.initState();
    // Restore a saved session on launch.
    Future.microtask(() => ref.read(authProvider.notifier).restore());
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    return MaterialApp(
      title: 'GOD MODE AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF6750A4),
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        colorSchemeSeed: const Color(0xFF6750A4),
        useMaterial3: true,
        brightness: Brightness.dark,
      ),
      home: auth.isAuthenticated ? const ChatScreen() : const LoginScreen(),
    );
  }
}
