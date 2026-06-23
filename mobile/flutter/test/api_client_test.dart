import 'package:flutter_test/flutter_test.dart';
import 'package:god_mode_ai/models/auth.dart';
import 'package:god_mode_ai/models/agent.dart';
import 'package:god_mode_ai/models/chat.dart';

void main() {
  test('AuthTokens parses login response', () {
    final t = AuthTokens.fromJson({
      'access_token': 'abc',
      'refresh_token': 'def',
      'user_id': 'u1',
      'token_type': 'bearer',
    });
    expect(t.accessToken, 'abc');
    expect(t.userId, 'u1');
  });

  test('AgentInfo parses roster entry', () {
    final a = AgentInfo.fromJson({'name': 'knowledge', 'tier': 'general', 'status': 'ready'});
    expect(a.tier, 'general');
  });

  test('ChatMessage round-trips through JSON', () {
    final m = ChatMessage(sender: Sender.king, text: 'hi', detail: {'steps_total': 2});
    final back = ChatMessage.fromJson(m.toJson());
    expect(back.sender, Sender.king);
    expect(back.detail!['steps_total'], 2);
  });
}
