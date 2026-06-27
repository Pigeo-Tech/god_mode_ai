import 'package:flutter/material.dart';

/// Buddy's visual identity — a dark UI with a purple→magenta gradient accent.
class BuddyColors {
  static const bg = Color(0xFF0B0710);
  static const bg2 = Color(0xFF120C1B);
  static const surface = Color(0xFF1A1322);
  static const surfaceHi = Color(0xFF241A30);
  static const purple = Color(0xFFA855F7);
  static const purpleDeep = Color(0xFF7C3AED);
  static const magenta = Color(0xFFC026D3);
  static const text = Color(0xFFF4EFFF);
  static const muted = Color(0xFF9A8FB0);

  static const accent = LinearGradient(
    colors: [magenta, purpleDeep],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  static const header = LinearGradient(
    colors: [Color(0xFF7C3AED), Color(0xFF3B1D6E), Color(0xFF0B0710)],
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
  );
}

ThemeData buddyTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: BuddyColors.purple,
    brightness: Brightness.dark,
  ).copyWith(
    primary: BuddyColors.purple,
    surface: BuddyColors.bg,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: BuddyColors.bg,
    colorScheme: scheme,
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: true,
      foregroundColor: BuddyColors.text,
    ),
    textTheme: const TextTheme().apply(
      bodyColor: BuddyColors.text,
      displayColor: BuddyColors.text,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: BuddyColors.surface,
      hintStyle: const TextStyle(color: BuddyColors.muted),
      labelStyle: const TextStyle(color: BuddyColors.muted),
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
      enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: BuddyColors.purple, width: 1.4),
      ),
    ),
  );
}

/// A filled pill button with the purple gradient.
class GradientButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  const GradientButton(
      {super.key, required this.label, this.onPressed, this.loading = false});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: loading ? null : onPressed,
      child: Container(
        height: 54,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          gradient: BuddyColors.accent,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: BuddyColors.purple.withOpacity(.35),
                blurRadius: 20,
                offset: const Offset(0, 8)),
          ],
        ),
        child: loading
            ? const SizedBox(
                height: 22, width: 22, child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
            : Text(label,
                style: const TextStyle(
                    color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700)),
      ),
    );
  }
}
