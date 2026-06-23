import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/chat.dart';
import 'server_config.dart';

/// Streams live King progress over WS /v1/stream.
class WsClient {
  /// Opens a socket, sends {token, message}, and yields parsed events until 'done'.
  Stream<StreamEvent> streamChat(String token, String message) async* {
    final channel = WebSocketChannel.connect(Uri.parse(ServerConfig.wsUrl));
    await channel.ready;
    channel.sink.add(jsonEncode({'token': token, 'message': message}));
    try {
      await for (final raw in channel.stream) {
        final map = jsonDecode(raw as String) as Map<String, dynamic>;
        final event = StreamEvent.fromJson(map);
        yield event;
        if (event.type == 'done' || event.type == 'error') break;
      }
    } finally {
      await channel.sink.close();
    }
  }
}
