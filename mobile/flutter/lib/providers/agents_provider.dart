import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/agent.dart';
import 'auth_provider.dart';

/// Loads the live agent roster from GET /v1/agents.
final agentsProvider = FutureProvider<List<AgentInfo>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.agents();
});
