import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/chat.dart';

/// Matches http(s) URLs inside the King's replies so they can be made tappable.
final _urlPattern = RegExp(r'(https?:\/\/[^\s]+)');

class MessageBubble extends StatelessWidget {
  final ChatMessage message;
  const MessageBubble({super.key, required this.message});

  Future<void> _open(String url) async {
    final uri = Uri.tryParse(url.replaceAll(RegExp(r'[.,)\]]+$'), ''));
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  /// Splits [text] into plain spans and tappable link spans.
  List<InlineSpan> _spans(BuildContext context) {
    final linkColor = Theme.of(context).colorScheme.primary;
    final spans = <InlineSpan>[];
    var index = 0;
    for (final match in _urlPattern.allMatches(text)) {
      if (match.start > index) {
        spans.add(TextSpan(text: text.substring(index, match.start)));
      }
      final url = match.group(0)!;
      spans.add(TextSpan(
        text: url,
        style: TextStyle(
          color: linkColor,
          decoration: TextDecoration.underline,
          fontWeight: FontWeight.w600,
        ),
        recognizer: TapGestureRecognizer()..onTap = () => _open(url),
      ));
      index = match.end;
    }
    if (index < text.length) {
      spans.add(TextSpan(text: text.substring(index)));
    }
    return spans;
  }

  String get text => message.text;

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == Sender.user;
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.all(12),
        constraints: const BoxConstraints(maxWidth: 320),
        decoration: BoxDecoration(
          color: isUser ? scheme.primaryContainer : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            RichText(
              text: TextSpan(
                style: DefaultTextStyle.of(context).style,
                children: _spans(context),
              ),
            ),
            if (message.detail != null) ...[
              const SizedBox(height: 6),
              Text(
                '${message.detail!['steps_completed'] ?? '?'}/'
                '${message.detail!['steps_total'] ?? '?'} subtasks',
                style: Theme.of(context).textTheme.labelSmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
