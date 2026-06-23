import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/offline_store.dart';
import '../core/ws_client.dart';
import '../models/chat.dart';
import 'auth_provider.dart';

final wsClientProvider = Provider<WsClient>((ref) => WsClient());
final offlineStoreProvider = Provider<OfflineStore>((ref) => OfflineStore());

class ChatState {
  final List<ChatMessage> messages;
  final bool streaming;
  final String? status; // last lifecycle status

  const ChatState({this.messages = const [], this.streaming = false, this.status});

  ChatState copyWith({List<ChatMessage>? messages, bool? streaming, String? status}) =>
      ChatState(
        messages: messages ?? this.messages,
        streaming: streaming ?? this.streaming,
        status: status ?? this.status,
      );
}

class ChatController extends StateNotifier<ChatState> {
  final WsClient _ws;
  final OfflineStore _store;
  final String Function() _token;

  ChatController(this._ws, this._store, this._token) : super(const ChatState()) {
    _restore();
  }

  Future<void> _restore() async {
    final history = await _store.loadHistory();
    state = state.copyWith(messages: history);
  }

  Future<void> send(String text) async {
    final outgoing = [...state.messages, ChatMessage(sender: Sender.user, text: text)];
    state = state.copyWith(messages: outgoing, streaming: true, status: 'sending');

    try {
      await for (final event in _ws.streamChat(_token(), text)) {
        if (event.type == 'progress') {
          state = state.copyWith(status: 'working');
        } else if (event.type == 'result') {
          final result = event.data['result'] as Map<String, dynamic>?;
          final summary = result?['summary']?.toString() ?? 'Done.';
          final msgs = [
            ...state.messages,
            ChatMessage(sender: Sender.king, text: summary, detail: result),
          ];
          state = state.copyWith(messages: msgs, status: 'completed');
          await _store.saveHistory(msgs);
        }
      }
    } catch (e) {
      final msgs = [
        ...state.messages,
        ChatMessage(sender: Sender.king, text: 'Error: $e'),
      ];
      state = state.copyWith(messages: msgs, status: 'error');
    } finally {
      state = state.copyWith(streaming: false);
    }
  }

  Future<void> clear() async {
    await _store.clear();
    state = const ChatState();
  }
}

final chatProvider = StateNotifierProvider<ChatController, ChatState>((ref) {
  final auth = ref.watch(authProvider);
  return ChatController(
    ref.watch(wsClientProvider),
    ref.watch(offlineStoreProvider),
    () => auth.tokens?.accessToken ?? '',
  );
});
