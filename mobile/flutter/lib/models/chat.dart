/// A chat message in the conversation (local model).
enum Sender { user, king }

class ChatMessage {
  final Sender sender;
  final String text;
  final DateTime at;
  final Map<String, dynamic>? detail; // King breakdown for assistant messages

  ChatMessage({
    required this.sender,
    required this.text,
    DateTime? at,
    this.detail,
  }) : at = at ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'sender': sender.name,
        'text': text,
        'at': at.toIso8601String(),
        'detail': detail,
      };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
        sender: Sender.values.firstWhere((s) => s.name == json['sender']),
        text: json['text'] as String,
        at: DateTime.tryParse(json['at'] as String? ?? ''),
        detail: json['detail'] as Map<String, dynamic>?,
      );
}

/// A streaming event from WS /v1/stream or the SSE chat endpoint.
class StreamEvent {
  final String type; // accepted | progress | result | done | error
  final Map<String, dynamic> data;
  StreamEvent(this.type, this.data);

  factory StreamEvent.fromJson(Map<String, dynamic> json) =>
      StreamEvent((json['type'] ?? 'unknown') as String, json);
}
