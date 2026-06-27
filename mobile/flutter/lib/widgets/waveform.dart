import 'dart:math';
import 'package:flutter/material.dart';

import '../theme.dart';

/// Animated purple voice waveform — shown while Buddy is listening / speaking.
class VoiceWaveform extends StatefulWidget {
  final bool active;
  final double height;
  const VoiceWaveform({super.key, this.active = true, this.height = 130});

  @override
  State<VoiceWaveform> createState() => _VoiceWaveformState();
}

class _VoiceWaveformState extends State<VoiceWaveform>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c =
      AnimationController(vsync: this, duration: const Duration(seconds: 3))..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height,
      width: double.infinity,
      child: AnimatedBuilder(
        animation: _c,
        builder: (_, __) => CustomPaint(
          painter: _WavePainter(_c.value, widget.active ? 1.0 : 0.22),
        ),
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final double t;
  final double amp;
  _WavePainter(this.t, this.amp);

  @override
  void paint(Canvas canvas, Size size) {
    final mid = size.height / 2;
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.6
      ..strokeCap = StrokeCap.round;

    final colors = [BuddyColors.magenta, BuddyColors.purple, BuddyColors.purpleDeep];
    final opacities = [0.95, 0.55, 0.3];
    for (var line = 0; line < 3; line++) {
      final path = Path();
      final phase = t * 2 * pi + line * 0.8;
      final a = amp * size.height * 0.34 * (1 - line * 0.22);
      paint.color = colors[line].withOpacity(opacities[line]);
      for (double x = 0; x <= size.width; x += 3) {
        final envelope = sin(x / size.width * pi); // taper at the edges
        final y = mid + sin((x / size.width * 4.5 * pi) + phase) * a * envelope;
        x == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
      }
      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter old) => true;
}
