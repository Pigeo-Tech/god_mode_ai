import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/agents_provider.dart';

class AgentsScreen extends ConsumerWidget {
  const AgentsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final agents = ref.watch(agentsProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Agents')),
      body: agents.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Failed to load: $e')),
        data: (list) => ListView.builder(
          itemCount: list.length,
          itemBuilder: (_, i) {
            final a = list[i];
            return ListTile(
              leading: CircleAvatar(child: Text(a.tier.substring(0, 1).toUpperCase())),
              title: Text(a.name),
              subtitle: Text(a.tier),
              trailing: Chip(label: Text(a.status)),
            );
          },
        ),
      ),
    );
  }
}
