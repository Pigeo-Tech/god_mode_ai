/// One live agent from GET /v1/agents.
class AgentInfo {
  final String name;
  final String tier;
  final String status;

  const AgentInfo({required this.name, required this.tier, required this.status});

  factory AgentInfo.fromJson(Map<String, dynamic> json) => AgentInfo(
        name: json['name'] as String,
        tier: json['tier'] as String,
        status: (json['status'] ?? 'unknown') as String,
      );
}
