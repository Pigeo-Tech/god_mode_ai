import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/auth_provider.dart';
import 'screens/chat_screen.dart';
import 'screens/login_screen.dart';
import 'screens/splash_screen.dart';
import 'theme.dart';

class GodModeApp extends ConsumerStatefulWidget {
  const GodModeApp({super.key});
  @override
  ConsumerState<GodModeApp> createState() => _GodModeAppState();
}

class _GodModeAppState extends ConsumerState<GodModeApp> {
  bool _showSplash = true;

  @override
  void initState() {
    super.initState();
    // Restore a saved session on launch, and show the splash for a short beat.
    Future.microtask(() => ref.read(authProvider.notifier).restore());
    Future.delayed(const Duration(milliseconds: 1800), () {
      if (mounted) setState(() => _showSplash = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    return MaterialApp(
      title: 'Buddy',
      debugShowCheckedModeBanner: false,
      theme: buddyTheme(),
      darkTheme: buddyTheme(),
      themeMode: ThemeMode.dark,
      home: _showSplash
          ? const SplashScreen()
          : (auth.isAuthenticated ? const ChatScreen() : const LoginScreen()),
    );
  }
}
