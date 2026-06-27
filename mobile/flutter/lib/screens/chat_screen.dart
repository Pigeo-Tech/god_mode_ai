import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../core/media_player.dart';
import '../models/chat.dart';
import '../providers/auth_provider.dart';
import '../providers/chat_provider.dart';
import '../theme.dart';
import '../widgets/message_bubble.dart';
import '../widgets/waveform.dart';
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
  final AudioPlayer _player = AudioPlayer(); // plays ElevenLabs MP3 from the backend
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
    _player.dispose();
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
    await _player.stop();
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

  /// Now-playing bar with play/pause + stop, shown while Buddy is playing music.
  Widget _miniPlayer(BuildContext context) {
    final p = BuddyPlayer.instance;
    return StreamBuilder<bool>(
      stream: p.playingStream,
      builder: (context, snap) {
        if (p.nowPlaying == null) return const SizedBox.shrink();
        final playing = snap.data ?? p.isPlaying;
        return Material(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: Row(children: [
              const Icon(Icons.music_note_rounded, size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Text(p.nowPlaying!,
                    maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
              IconButton(
                icon: Icon(playing ? Icons.pause_rounded : Icons.play_arrow_rounded),
                onPressed: () => p.toggle(),
              ),
              IconButton(
                icon: const Icon(Icons.stop_rounded),
                onPressed: () async {
                  await p.stop();
                  if (mounted) setState(() {});
                },
              ),
            ]),
          ),
        );
      },
    );
  }

  Future<void> _speak(String text) async {
    if (!_voiceReplies) return;
    final clean = text.replaceAll(RegExp(r'https?://\S+'), '').trim();
    if (clean.isEmpty) return;
    final speech = clean.length > 700 ? clean.substring(0, 700) : clean;
    await _tts.stop();
    await _player.stop();
    // Prefer the natural ElevenLabs voice from the backend; fall back to device TTS.
    final bytes = await ref.read(apiClientProvider).tts(speech);
    if (bytes != null) {
      try {
        await _player.play(BytesSource(Uint8List.fromList(bytes)));
        return;
      } catch (_) {/* fall back to device TTS below */}
    }
    await _tts.speak(speech);
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
        title: Row(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 30,
            height: 30,
            decoration: const BoxDecoration(
                gradient: BuddyColors.accent, shape: BoxShape.circle),
            child: const Icon(Icons.auto_awesome, size: 16, color: Colors.white),
          ),
          const SizedBox(width: 10),
          const Text('Talk to Buddy', style: TextStyle(fontWeight: FontWeight.w700)),
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
          _miniPlayer(context),
          if (_listening) const VoiceWaveform(active: true, height: 90),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 6, 12, 12),
              child: Row(children: [
                Expanded(
                  child: TextField(
                    controller: _input,
                    onSubmitted: (_) => _send(),
                    style: const TextStyle(color: BuddyColors.text),
                    decoration: InputDecoration(
                      hintText: _listening ? "I'm listening…" : 'Ask Buddy anything…',
                      suffixIcon: IconButton(
                        icon: Icon(chat.streaming ? Icons.hourglass_empty : Icons.send_rounded,
                            color: BuddyColors.purple),
                        onPressed: chat.streaming ? null : _send,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _toggleMic,
                  child: Container(
                    width: 54,
                    height: 54,
                    decoration: BoxDecoration(
                      gradient: BuddyColors.accent,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                            color: BuddyColors.purple.withOpacity(_listening ? .6 : .3),
                            blurRadius: _listening ? 26 : 14),
                      ],
                    ),
                    child: Icon(_listening ? Icons.stop_rounded : Icons.mic_rounded,
                        color: Colors.white, size: 26),
                  ),
                ),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _empty(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: BuddyColors.accent,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text('Hey 👋',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(height: 20),
            const Text('What can I', style: TextStyle(fontSize: 26, color: BuddyColors.muted)),
            const Text('help you with?',
                style: TextStyle(
                    fontSize: 28, fontWeight: FontWeight.w800, color: BuddyColors.text)),
            const SizedBox(height: 26),
            VoiceWaveform(active: _listening, height: 120),
            const SizedBox(height: 26),
            Text(
              'Tap the mic or type. Try "play a Tamil song", '
              '"latest AI news", or "book a movie ticket".',
              textAlign: TextAlign.center,
              style: const TextStyle(color: BuddyColors.muted),
            ),
          ],
        ),
      );
}
