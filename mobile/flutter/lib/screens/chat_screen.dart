import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../models/chat.dart';
import '../providers/auth_provider.dart';
import '../providers/chat_provider.dart';
import '../widgets/message_bubble.dart';
import 'agents_screen.dart';

/// Buddy — the friendly user-facing AI chat bot. Buddy is not an agent: it takes the user's
/// voice/text request, sends it to the King, and shows or speaks the final answer.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});
  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _input = TextEditingController();
  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();
  bool _listening = false;
  bool _voiceReplies = true;
  int _spoken = 0; // how many King replies we've already spoken

  @override
  void initState() {
    super.initState();
    _tts.setSpeechRate(0.5);
    _tts.setPitch(1.05);
  }

  @override
  void dispose() {
    _tts.stop();
    _input.dispose();
    super.dispose();
  }

  Future<void> _toggleMic() async {
    if (_listening) {
      await _speech.stop();
      setState(() => _listening = false);
      return;
    }
    await _tts.stop();
    final ok = await _speech.initialize(
      onError: (_) => setState(() => _listening = false),
      onStatus: (s) {
        if (s == 'done' || s == 'notListening') setState(() => _listening = false);
      },
    );
    if (!ok) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission needed for voice')));
      }
      return;
    }
    setState(() => _listening = true);
    _speech.listen(onResult: (r) {
      setState(() => _input.text = r.recognizedWords);
      if (r.finalResult && _input.text.trim().isNotEmpty) {
        setState(() => _listening = false);
        _send();
      }
    });
  }

  void _send() {
    final text = _input.text.trim();
    if (text.isEmpty) return;
    ref.read(chatProvider.notifier).send(text);
    _input.clear();
  }

  Future<void> _speak(String text) async {
    if (!_voiceReplies) return;
    final clean = text.replaceAll(RegExp(r'https?://\S+'), '').trim();
    if (clean.isEmpty) return;
    await _tts.stop();
    await _tts.speak(clean.length > 700 ? clean.substring(0, 700) : clean);
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatProvider);

    // Speak each new King reply aloud (but never replay restored history).
    ref.listen(chatProvider, (prev, next) {
      final kings = next.messages.where((m) => m.sender == Sender.king).length;
      if (prev == null) {
        _spoken = kings;
        return;
      }
      if (kings > _spoken && !next.streaming) {
        _spoken = kings;
        final last = next.messages.lastWhere((m) => m.sender == Sender.king);
        _speak(last.text);
      }
    });

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 12,
        title: Row(children: [
          const CircleAvatar(radius: 14, child: Icon(Icons.smart_toy_rounded, size: 18)),
          const SizedBox(width: 10),
          const Text('Buddy'),
        ]),
        actions: [
          IconButton(
            icon: Icon(_voiceReplies ? Icons.volume_up_rounded : Icons.volume_off_rounded),
            tooltip: _voiceReplies ? 'Voice replies on' : 'Voice replies off',
            onPressed: () => setState(() => _voiceReplies = !_voiceReplies),
          ),
          IconButton(
            icon: const Icon(Icons.account_tree_outlined),
            tooltip: 'Agents',
            onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AgentsScreen())),
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
            onPressed: () => ref.read(authProvider.notifier).logout(),
          ),
        ],
      ),
      body: Column(
        children: [
          if (chat.streaming) const LinearProgressIndicator(value: null, minHeight: 2),
          Expanded(
            child: chat.messages.isEmpty
                ? _empty(context)
                : ListView.builder(
                    itemCount: chat.messages.length,
                    itemBuilder: (_, i) => MessageBubble(message: chat.messages[i]),
                  ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: Row(children: [
                IconButton.filledTonal(
                  onPressed: _toggleMic,
                  isSelected: _listening,
                  icon: Icon(_listening ? Icons.mic : Icons.mic_none_rounded),
                  tooltip: _listening ? 'Listening… tap to stop' : 'Speak to Buddy',
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _input,
                    onSubmitted: (_) => _send(),
                    decoration: InputDecoration(
                      hintText: _listening ? 'Listening…' : 'Ask Buddy anything…',
                      border: const OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: chat.streaming ? null : _send,
                  icon: const Icon(Icons.send),
                ),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _empty(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const CircleAvatar(radius: 30, child: Icon(Icons.smart_toy_rounded, size: 30)),
            const SizedBox(height: 16),
            Text('Hi, I\'m Buddy', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(
              'Talk or type, and I\'ll get it done. Try "play a Tamil song", '
              '"what\'s the latest AI news", or "book a movie ticket".',
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).hintColor),
            ),
          ]),
        ),
      );
}
