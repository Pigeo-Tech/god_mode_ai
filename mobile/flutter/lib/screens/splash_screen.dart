import 'package:flutter/material.dart';

import '../theme.dart';

/// Branded purple splash shown briefly on launch.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: BuddyColors.accent),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(.14),
                  borderRadius: BorderRadius.circular(28),
                  border: Border.all(color: Colors.white.withOpacity(.35), width: 1.5),
                ),
                child: const Icon(Icons.auto_awesome, color: Colors.white, size: 46),
              ),
              const SizedBox(height: 22),
              const Text('BUDDY',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 30,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 6)),
              const SizedBox(height: 8),
              Text('Your AGNI assistant',
                  style: TextStyle(color: Colors.white.withOpacity(.8), letterSpacing: 1)),
              const SizedBox(height: 36),
              const SizedBox(
                width: 26,
                height: 26,
                child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
