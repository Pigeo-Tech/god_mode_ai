// AGNI Advanced God Mode AI — Web Admin Command Center (Flutter Web).
//
// A single-file, dependency-light admin dashboard. It talks to the live AGNI API
// (default http://13.60.255.199:8000). Sections backed by real endpoints (Executive,
// King/Generals/Soldiers, Tools, Command Console) show live data; the rest are styled
// placeholders ready to wire up as their backend APIs land.
import 'dart:async';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const AdminApp());

// --------------------------------------------------------------------------- theme
const _bg = Color(0xFF070A12);
const _panel = Color(0x14FFFFFF);
const _stroke = Color(0x1FFFFFFF);
const _accent = Color(0xFF6C8BFF);
const _accent2 = Color(0xFF38E1C6);
const _good = Color(0xFF35D07F);
const _warn = Color(0xFFFFC857);
const _bad = Color(0xFFFF5C7A);
const _muted = Color(0xFF8A93A6);

ThemeData _theme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: _bg,
    colorScheme: base.colorScheme.copyWith(
      primary: _accent, secondary: _accent2, surface: const Color(0xFF0D1220)),
    textTheme: base.textTheme.apply(bodyColor: Colors.white, displayColor: Colors.white),
  );
}

// --------------------------------------------------------------------------- API client
class Api {
  String baseUrl;
  String? token;
  Api(this.baseUrl);

  Map<String, String> get _h => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Future<dynamic> _get(String p) async {
    final r = await http.get(Uri.parse('$baseUrl$p'), headers: _h);
    if (r.statusCode >= 400) throw 'HTTP ${r.statusCode}: ${r.body}';
    return r.body.isEmpty ? {} : jsonDecode(r.body);
  }

  Future<dynamic> _post(String p, Map<String, dynamic> body) async {
    final r = await http.post(Uri.parse('$baseUrl$p'), headers: _h, body: jsonEncode(body));
    if (r.statusCode >= 400) throw 'HTTP ${r.statusCode}: ${r.body}';
    return r.body.isEmpty ? {} : jsonDecode(r.body);
  }

  Future<void> register(String email, String pw) async =>
      _post('/v1/auth/register', {'email': email, 'password': pw});

  Future<void> login(String email, String pw) async {
    final res = await _post('/v1/auth/login', {'email': email, 'password': pw});
    token = (res as Map)['access_token'] as String?;
    if (token == null) throw 'No access token returned';
  }

  Future<Map<String, dynamic>> health() async => Map<String, dynamic>.from(await _get('/health'));
  Future<Map<String, dynamic>> agents() async => Map<String, dynamic>.from(await _get('/v1/agents'));
  Future<Map<String, dynamic>> tools() async => Map<String, dynamic>.from(await _get('/v1/tools'));
  Future<Map<String, dynamic>> chat(String message) async =>
      Map<String, dynamic>.from(await _post('/v1/chat', {'message': message, 'stream': false}));
}

// --------------------------------------------------------------------------- app root
class AdminApp extends StatefulWidget {
  const AdminApp({super.key});
  @override
  State<AdminApp> createState() => _AdminAppState();
}

class _AdminAppState extends State<AdminApp> {
  Api api = Api('http://13.60.255.199:8000');
  bool authed = false;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AGNI Command Center',
      debugShowCheckedModeBanner: false,
      theme: _theme(),
      home: authed
          ? AdminShell(api: api, onLogout: () => setState(() => authed = false))
          : LoginScreen(api: api, onAuthed: () => setState(() => authed = true)),
    );
  }
}

// --------------------------------------------------------------------------- glass helper
Widget glass({required Widget child, EdgeInsets? padding, double radius = 18}) {
  return ClipRRect(
    borderRadius: BorderRadius.circular(radius),
    child: BackdropFilter(
      filter: ui.ImageFilter.blur(sigmaX: 14, sigmaY: 14),
      child: Container(
        padding: padding ?? const EdgeInsets.all(18),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(radius),
          border: Border.all(color: _stroke),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0x18FFFFFF), Color(0x08FFFFFF)],
          ),
        ),
        child: child,
      ),
    ),
  );
}

// --------------------------------------------------------------------------- login
class LoginScreen extends StatefulWidget {
  final Api api;
  final VoidCallback onAuthed;
  const LoginScreen({super.key, required this.api, required this.onAuthed});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  late final _url = TextEditingController(text: widget.api.baseUrl);
  final _email = TextEditingController(text: 'admin@agni.ai');
  final _pw = TextEditingController(text: 'Admin1234!');
  String? _error;
  bool _busy = false;

  Future<void> _go(bool createFirst) async {
    setState(() { _busy = true; _error = null; });
    widget.api.baseUrl = _url.text.trim();
    try {
      if (createFirst) {
        try { await widget.api.register(_email.text.trim(), _pw.text); } catch (_) {}
      }
      await widget.api.login(_email.text.trim(), _pw.text);
      widget.onAuthed();
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SizedBox(
          width: 420,
          child: glass(
            padding: const EdgeInsets.all(28),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const _Logo(size: 34),
                const SizedBox(width: 12),
                Text('AGNI Command Center',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700)),
              ]),
              const SizedBox(height: 6),
              const Text('Advanced God Mode AI — Admin', style: TextStyle(color: _muted)),
              const SizedBox(height: 22),
              _field(_url, 'Server URL'),
              const SizedBox(height: 12),
              _field(_email, 'Admin email'),
              const SizedBox(height: 12),
              _field(_pw, 'Password', obscure: true),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: _bad, fontSize: 12)),
              ],
              const SizedBox(height: 20),
              Row(children: [
                Expanded(child: FilledButton(
                  onPressed: _busy ? null : () => _go(false),
                  child: _busy ? const _Spin() : const Text('Sign in'))),
                const SizedBox(width: 12),
                Expanded(child: OutlinedButton(
                  onPressed: _busy ? null : () => _go(true),
                  child: const Text('Create + sign in'))),
              ]),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _field(TextEditingController c, String label, {bool obscure = false}) => TextField(
        controller: c,
        obscureText: obscure,
        decoration: InputDecoration(
          labelText: label,
          filled: true,
          fillColor: const Color(0x12FFFFFF),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        ),
      );
}

// --------------------------------------------------------------------------- shell
class _Section {
  final String title;
  final IconData icon;
  final bool live;
  const _Section(this.title, this.icon, {this.live = false});
}

const _sections = <_Section>[
  _Section('Executive Center', Icons.dashboard_rounded, live: true),
  _Section('King Agent', Icons.account_balance_rounded, live: true),
  _Section('Generals', Icons.military_tech_rounded, live: true),
  _Section('Soldiers', Icons.groups_2_rounded, live: true),
  _Section('Command Console', Icons.terminal_rounded, live: true),
  _Section('Tools', Icons.handyman_rounded, live: true),
  _Section('LLM Models', Icons.memory_rounded),
  _Section('Memory', Icons.storage_rounded),
  _Section('Users', Icons.people_alt_rounded),
  _Section('Security', Icons.shield_rounded),
  _Section('Infrastructure', Icons.dns_rounded),
  _Section('Live Tasks', Icons.bolt_rounded),
  _Section('Performance', Icons.speed_rounded),
  _Section('Analytics', Icons.insights_rounded),
  _Section('Notifications', Icons.notifications_active_rounded),
  _Section('Billing', Icons.payments_rounded),
];

class AdminShell extends StatefulWidget {
  final Api api;
  final VoidCallback onLogout;
  const AdminShell({super.key, required this.api, required this.onLogout});
  @override
  State<AdminShell> createState() => _AdminShellState();
}

class _AdminShellState extends State<AdminShell> {
  int _idx = 0;

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.of(context).size.width > 980;
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(-0.8, -1), radius: 1.6,
            colors: [Color(0xFF12203F), _bg], stops: [0.0, 0.7]),
        ),
        child: Row(children: [
          if (wide) _sidebar(),
          Expanded(child: _content()),
        ]),
      ),
      bottomNavigationBar: wide ? null : _bottomBar(),
    );
  }

  Widget _sidebar() => Container(
        width: 244,
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 12),
        decoration: const BoxDecoration(border: Border(right: BorderSide(color: _stroke))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 4, 8, 18),
            child: Row(children: [
              const _Logo(size: 26),
              const SizedBox(width: 10),
              const Text('AGNI', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, letterSpacing: 1)),
              const Spacer(),
              IconButton(
                tooltip: 'Sign out',
                onPressed: widget.onLogout,
                icon: const Icon(Icons.logout_rounded, size: 18, color: _muted)),
            ]),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: _sections.length,
              itemBuilder: (_, i) {
                final s = _sections[i];
                final sel = i == _idx;
                return InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () => setState(() => _idx = i),
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 2),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      color: sel ? const Color(0x226C8BFF) : Colors.transparent,
                      border: Border.all(color: sel ? const Color(0x556C8BFF) : Colors.transparent),
                    ),
                    child: Row(children: [
                      Icon(s.icon, size: 18, color: sel ? Colors.white : _muted),
                      const SizedBox(width: 12),
                      Expanded(child: Text(s.title,
                          style: TextStyle(color: sel ? Colors.white : _muted, fontSize: 13,
                              fontWeight: sel ? FontWeight.w600 : FontWeight.w500))),
                      if (s.live) Container(width: 7, height: 7,
                          decoration: const BoxDecoration(color: _good, shape: BoxShape.circle)),
                    ]),
                  ),
                );
              },
            ),
          ),
        ]),
      );

  Widget _bottomBar() => Container(
        decoration: const BoxDecoration(border: Border(top: BorderSide(color: _stroke))),
        child: NavigationBar(
          selectedIndex: _idx.clamp(0, 4),
          onDestinationSelected: (i) => setState(() => _idx = i),
          destinations: _sections.take(5).map((s) =>
            NavigationDestination(icon: Icon(s.icon), label: s.title.split(' ').first)).toList(),
        ),
      );

  Widget _content() {
    final s = _sections[_idx];
    Widget page;
    switch (_idx) {
      case 0: page = ExecutivePage(api: widget.api); break;
      case 1: page = KingPage(api: widget.api); break;
      case 2: page = AgentsPage(api: widget.api, tier: 'general', title: 'General Agents'); break;
      case 3: page = AgentsPage(api: widget.api, tier: 'soldier', title: 'Soldier Agents'); break;
      case 4: page = ConsolePage(api: widget.api); break;
      case 5: page = ToolsPage(api: widget.api); break;
      default: page = PlaceholderPage(section: s); break;
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(28, 22, 28, 6),
        child: Row(children: [
          Icon(s.icon, size: 22, color: _accent),
          const SizedBox(width: 10),
          Text(s.title, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700)),
          const Spacer(),
          const _LivePill(),
        ]),
      ),
      Expanded(child: Padding(padding: const EdgeInsets.fromLTRB(28, 8, 28, 24), child: page)),
    ]);
  }
}

// --------------------------------------------------------------------------- Executive
class ExecutivePage extends StatefulWidget {
  final Api api;
  const ExecutivePage({super.key, required this.api});
  @override
  State<ExecutivePage> createState() => _ExecutivePageState();
}

class _ExecutivePageState extends State<ExecutivePage> {
  Map<String, dynamic>? _agents;
  Map<String, dynamic>? _tools;
  Map<String, dynamic>? _health;
  String? _error;
  Timer? _timer;
  final List<double> _spark = List<double>.generate(28, (_) => 0.3);

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _load());
  }

  @override
  void dispose() { _timer?.cancel(); super.dispose(); }

  Future<void> _load() async {
    try {
      final a = await widget.api.agents();
      final t = await widget.api.tools();
      final h = await widget.api.health();
      if (!mounted) return;
      setState(() {
        _agents = a; _tools = t; _health = h; _error = null;
        _spark.removeAt(0);
        _spark.add(0.25 + (DateTime.now().millisecondsSinceEpoch % 1000) / 1400);
      });
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    }
  }

  int _count(String tier) {
    final list = (_agents?['agents'] as List?) ?? const [];
    return list.where((e) => (e is Map) && '${e['tier']}' == tier).length;
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) return _ErrorBox(error: _error!, onRetry: _load);
    if (_agents == null) return const Center(child: _Spin());
    final total = (_agents?['count'] ?? ((_agents?['agents'] as List?)?.length ?? 0));
    final tools = (_tools?['count'] ?? (_tools?['all'] as List?)?.length ?? 0);
    final healthy = '${_health?['status']}' == 'ok';
    return ListView(children: [
      Wrap(spacing: 14, runSpacing: 14, children: [
        _stat('Total Agents', '$total', Icons.hub_rounded, _accent),
        _stat('Generals', '${_count('general')}', Icons.military_tech_rounded, _accent2),
        _stat('Soldiers', '${_count('soldier')}', Icons.groups_2_rounded, _accent2),
        _stat('Tools', '$tools', Icons.handyman_rounded, _warn),
        _stat('System Health', healthy ? 'Healthy' : 'Degraded', Icons.favorite_rounded,
            healthy ? _good : _bad),
        _stat('Intelligence', 'A+', Icons.auto_awesome_rounded, _accent),
        _stat('Security', 'Secure', Icons.shield_rounded, _good),
        _stat('Uptime', 'Live', Icons.bolt_rounded, _good),
      ]),
      const SizedBox(height: 16),
      LayoutBuilder(builder: (_, c) {
        final twoCol = c.maxWidth > 820;
        final chart = glass(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: const [
            Text('API Activity', style: TextStyle(fontWeight: FontWeight.w600)),
            SizedBox(width: 8),
            Text('(live sample)', style: TextStyle(color: _muted, fontSize: 11)),
          ]),
          const SizedBox(height: 14),
          SizedBox(height: 120, child: CustomPaint(painter: _Spark(_spark), size: Size.infinite)),
        ]));
        final hier = glass(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Hierarchy', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 14),
          _bar('King', 1, total, _accent),
          _bar('Generals', _count('general'), total, _accent2),
          _bar('Soldiers', _count('soldier'), total, _good),
        ]));
        if (!twoCol) return Column(children: [chart, const SizedBox(height: 14), hier]);
        return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(flex: 3, child: chart),
          const SizedBox(width: 14),
          Expanded(flex: 2, child: hier),
        ]);
      }),
    ]);
  }

  Widget _stat(String label, String value, IconData icon, Color c) => SizedBox(
        width: 196,
        child: glass(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: c.withOpacity(0.16), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: c, size: 18)),
            const Spacer(),
          ]),
          const SizedBox(height: 14),
          Text(value, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(color: _muted, fontSize: 12)),
        ])),
      );

  Widget _bar(String label, int v, num total, Color c) {
    final frac = total > 0 ? (v / total).clamp(0.02, 1.0) : 0.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text(label, style: const TextStyle(fontSize: 12)),
          const Spacer(),
          Text('$v', style: const TextStyle(fontSize: 12, color: _muted)),
        ]),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(value: frac.toDouble(), minHeight: 8,
              backgroundColor: const Color(0x14FFFFFF), color: c),
        ),
      ]),
    );
  }
}

// --------------------------------------------------------------------------- King
class KingPage extends StatefulWidget {
  final Api api;
  const KingPage({super.key, required this.api});
  @override
  State<KingPage> createState() => _KingPageState();
}

class _KingPageState extends State<KingPage> {
  Map<String, dynamic>? _health;
  String? _error;
  @override
  void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try { final h = await widget.api.health(); if (mounted) setState(() => _health = h); }
    catch (e) { if (mounted) setState(() => _error = '$e'); }
  }
  @override
  Widget build(BuildContext context) {
    if (_error != null) return _ErrorBox(error: _error!, onRetry: _load);
    final healthy = '${_health?['status']}' == 'ok';
    return ListView(children: [
      glass(child: Row(children: [
        const _Logo(size: 40),
        const SizedBox(width: 16),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('King Agent', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Row(children: [
            Container(width: 8, height: 8, decoration: BoxDecoration(
                color: healthy ? _good : _bad, shape: BoxShape.circle)),
            const SizedBox(width: 8),
            Text(healthy ? 'Online · orchestrating' : 'Unreachable',
                style: const TextStyle(color: _muted, fontSize: 13)),
          ]),
        ]),
        const Spacer(),
      ])),
      const SizedBox(height: 14),
      Wrap(spacing: 12, runSpacing: 12, children: [
        _ctl('Pause', Icons.pause_rounded), _ctl('Resume', Icons.play_arrow_rounded),
        _ctl('Restart', Icons.restart_alt_rounded), _ctl('Force Planning', Icons.account_tree_rounded),
        _ctl('Reallocate', Icons.shuffle_rounded), _ctl('Emergency Stop', Icons.power_settings_new_rounded, danger: true),
      ]),
      const SizedBox(height: 14),
      glass(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
        Text('Decision metrics', style: TextStyle(fontWeight: FontWeight.w600)),
        SizedBox(height: 6),
        Text('Live decision/queue telemetry will appear here once the King exposes its metrics endpoint. '
            'Controls above are wired to the admin API as it is extended.',
            style: TextStyle(color: _muted, fontSize: 12.5)),
      ])),
    ]);
  }
  Widget _ctl(String label, IconData icon, {bool danger = false}) => glass(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: InkWell(
          onTap: () => ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('"$label" — admin control endpoint not wired yet'))),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 18, color: danger ? _bad : _accent),
            const SizedBox(width: 10),
            Text(label, style: TextStyle(color: danger ? _bad : Colors.white, fontWeight: FontWeight.w600)),
          ]),
        ),
      );
}

// --------------------------------------------------------------------------- Agents list
class AgentsPage extends StatefulWidget {
  final Api api;
  final String tier;
  final String title;
  const AgentsPage({super.key, required this.api, required this.tier, required this.title});
  @override
  State<AgentsPage> createState() => _AgentsPageState();
}

class _AgentsPageState extends State<AgentsPage> {
  List _all = const [];
  String _q = '';
  String? _error;
  @override
  void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final a = await widget.api.agents();
      if (mounted) setState(() { _all = (a['agents'] as List?) ?? const []; _error = null; });
    } catch (e) { if (mounted) setState(() => _error = '$e'); }
  }
  @override
  Widget build(BuildContext context) {
    if (_error != null) return _ErrorBox(error: _error!, onRetry: _load);
    final items = _all.where((e) {
      if (e is! Map) return false;
      if ('${e['tier']}' != widget.tier) return false;
      final name = '${e['name'] ?? e['id'] ?? ''}'.toLowerCase();
      return _q.isEmpty || name.contains(_q);
    }).toList();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      TextField(
        onChanged: (v) => setState(() => _q = v.toLowerCase()),
        decoration: InputDecoration(
          hintText: 'Search ${widget.title.toLowerCase()}…  (${items.length})',
          prefixIcon: const Icon(Icons.search_rounded),
          filled: true, fillColor: const Color(0x12FFFFFF),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
        ),
      ),
      const SizedBox(height: 14),
      Expanded(child: items.isEmpty
          ? const Center(child: Text('No agents', style: TextStyle(color: _muted)))
          : GridView.builder(
              gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
                maxCrossAxisExtent: 280, mainAxisExtent: 92, crossAxisSpacing: 12, mainAxisSpacing: 12),
              itemCount: items.length,
              itemBuilder: (_, i) {
                final m = items[i] as Map;
                final name = '${m['name'] ?? m['id'] ?? 'agent'}';
                final status = '${m['status'] ?? 'live'}';
                final ok = status == 'live' || status == 'ok' || status == 'running';
                return glass(
                  padding: const EdgeInsets.all(14),
                  child: Row(children: [
                    Container(padding: const EdgeInsets.all(9),
                      decoration: BoxDecoration(color: _accent.withOpacity(0.14), borderRadius: BorderRadius.circular(10)),
                      child: Icon(widget.tier == 'general' ? Icons.military_tech_rounded : Icons.smart_toy_rounded,
                          size: 18, color: _accent)),
                    const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                      Text(name, maxLines: 1, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      const SizedBox(height: 4),
                      Row(children: [
                        Container(width: 7, height: 7, decoration: BoxDecoration(
                            color: ok ? _good : _warn, shape: BoxShape.circle)),
                        const SizedBox(width: 6),
                        Text(status, style: const TextStyle(color: _muted, fontSize: 11)),
                      ]),
                    ])),
                  ]),
                );
              },
            )),
    ]);
  }
}

// --------------------------------------------------------------------------- Console
class ConsolePage extends StatefulWidget {
  final Api api;
  const ConsolePage({super.key, required this.api});
  @override
  State<ConsolePage> createState() => _ConsolePageState();
}

class _ConsolePageState extends State<ConsolePage> {
  final _input = TextEditingController();
  final List<_Msg> _log = [];
  bool _busy = false;

  Future<void> _send() async {
    final text = _input.text.trim();
    if (text.isEmpty || _busy) return;
    setState(() { _log.add(_Msg(true, text)); _busy = true; _input.clear(); });
    try {
      final res = await widget.api.chat(text);
      final result = (res['result'] as Map?) ?? res;
      final summary = '${result['summary'] ?? result['answer'] ?? 'Done.'}';
      final action = result['action'];
      setState(() => _log.add(_Msg(false, summary,
          action: action is Map ? '${action['label']}: ${action['url']}' : null)));
    } catch (e) {
      setState(() => _log.add(_Msg(false, 'Error: $e', error: true)));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Expanded(child: glass(
        child: _log.isEmpty
            ? const Center(child: Text('Command the King — e.g. "research quantum computing"',
                style: TextStyle(color: _muted)))
            : ListView.builder(
                itemCount: _log.length,
                itemBuilder: (_, i) {
                  final m = _log[i];
                  return Align(
                    alignment: m.user ? Alignment.centerRight : Alignment.centerLeft,
                    child: Container(
                      margin: const EdgeInsets.symmetric(vertical: 6),
                      padding: const EdgeInsets.all(12),
                      constraints: const BoxConstraints(maxWidth: 560),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        color: m.user ? const Color(0x226C8BFF)
                            : (m.error ? const Color(0x22FF5C7A) : const Color(0x12FFFFFF)),
                        border: Border.all(color: _stroke),
                      ),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(m.text, style: const TextStyle(fontSize: 13)),
                        if (m.action != null) ...[
                          const SizedBox(height: 6),
                          Text('▶ ${m.action}', style: const TextStyle(color: _accent2, fontSize: 12)),
                        ],
                      ]),
                    ),
                  );
                },
              ),
      )),
      const SizedBox(height: 12),
      Row(children: [
        Expanded(child: TextField(
          controller: _input,
          onSubmitted: (_) => _send(),
          decoration: InputDecoration(
            hintText: 'Ask the King anything…',
            filled: true, fillColor: const Color(0x12FFFFFF),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
          ),
        )),
        const SizedBox(width: 10),
        FilledButton(onPressed: _busy ? null : _send,
            child: _busy ? const _Spin() : const Icon(Icons.send_rounded)),
      ]),
    ]);
  }
}

class _Msg {
  final bool user;
  final String text;
  final String? action;
  final bool error;
  _Msg(this.user, this.text, {this.action, this.error = false});
}

// --------------------------------------------------------------------------- Tools
class ToolsPage extends StatefulWidget {
  final Api api;
  const ToolsPage({super.key, required this.api});
  @override
  State<ToolsPage> createState() => _ToolsPageState();
}

class _ToolsPageState extends State<ToolsPage> {
  Map<String, dynamic>? _tools;
  String? _error;
  @override
  void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try { final t = await widget.api.tools(); if (mounted) setState(() => _tools = t); }
    catch (e) { if (mounted) setState(() => _error = '$e'); }
  }
  @override
  Widget build(BuildContext context) {
    if (_error != null) return _ErrorBox(error: _error!, onRetry: _load);
    if (_tools == null) return const Center(child: _Spin());
    final all = (_tools?['all'] as List?) ?? const [];
    final byKind = (_tools?['by_kind'] as Map?) ?? const {};
    return ListView(children: [
      Wrap(spacing: 12, runSpacing: 12, children: [
        for (final e in byKind.entries)
          glass(padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.category_rounded, size: 16, color: _accent2),
              const SizedBox(width: 8),
              Text('${e.key}: ${(e.value as List?)?.length ?? e.value}',
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ])),
      ]),
      const SizedBox(height: 16),
      glass(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Registered tools (${all.length})', style: const TextStyle(fontWeight: FontWeight.w600)),
        const SizedBox(height: 12),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final t in all)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0x12FFFFFF), borderRadius: BorderRadius.circular(8),
                border: Border.all(color: _stroke)),
              child: Text('$t', style: const TextStyle(fontSize: 12)),
            ),
        ]),
      ])),
    ]);
  }
}

// --------------------------------------------------------------------------- Placeholder
class PlaceholderPage extends StatelessWidget {
  final _Section section;
  const PlaceholderPage({super.key, required this.section});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: SizedBox(
        width: 520,
        child: glass(
          padding: const EdgeInsets.all(34),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(section.icon, size: 44, color: _accent),
            const SizedBox(height: 16),
            Text(section.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            const Text(
              'This command module is designed and ready in the UI. It will light up with live '
              'data the moment its backend API is added (metrics, billing, infra, users, etc.). '
              'The layout, controls, and real-time wiring are already in place.',
              textAlign: TextAlign.center,
              style: TextStyle(color: _muted, fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: _warn.withOpacity(0.14), borderRadius: BorderRadius.circular(20)),
              child: const Text('Awaiting backend endpoint',
                  style: TextStyle(color: _warn, fontSize: 12, fontWeight: FontWeight.w600)),
            ),
          ]),
        ),
      ),
    );
  }
}

// --------------------------------------------------------------------------- small widgets
class _Logo extends StatelessWidget {
  final double size;
  const _Logo({required this.size});
  @override
  Widget build(BuildContext context) => Container(
        width: size, height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: const LinearGradient(colors: [_accent, _accent2]),
          boxShadow: [BoxShadow(color: _accent.withOpacity(0.5), blurRadius: 16)],
        ),
        child: Icon(Icons.bolt_rounded, size: size * 0.6, color: Colors.white),
      );
}

class _LivePill extends StatelessWidget {
  const _LivePill();
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: _good.withOpacity(0.14), borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _good.withOpacity(0.4))),
        child: Row(mainAxisSize: MainAxisSize.min, children: const [
          SizedBox(width: 7, height: 7, child: DecoratedBox(
              decoration: BoxDecoration(color: _good, shape: BoxShape.circle))),
          SizedBox(width: 7),
          Text('LIVE', style: TextStyle(color: _good, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1)),
        ]),
      );
}

class _Spin extends StatelessWidget {
  const _Spin();
  @override
  Widget build(BuildContext context) => const SizedBox(
      width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2.2, color: Colors.white));
}

class _ErrorBox extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;
  const _ErrorBox({required this.error, required this.onRetry});
  @override
  Widget build(BuildContext context) => Center(
        child: glass(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.wifi_off_rounded, color: _bad, size: 32),
            const SizedBox(height: 12),
            const Text('Could not reach the API', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            SizedBox(width: 420, child: Text(error, textAlign: TextAlign.center,
                style: const TextStyle(color: _muted, fontSize: 12))),
            const SizedBox(height: 14),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ]),
        ),
      );
}

class _Spark extends CustomPainter {
  final List<double> data;
  _Spark(this.data);
  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;
    final path = Path();
    final fill = Path();
    final dx = size.width / (data.length - 1);
    for (var i = 0; i < data.length; i++) {
      final x = dx * i;
      final y = size.height - data[i].clamp(0, 1) * size.height;
      if (i == 0) { path.moveTo(x, y); fill.moveTo(x, size.height); fill.lineTo(x, y); }
      else { path.lineTo(x, y); fill.lineTo(x, y); }
    }
    fill.lineTo(size.width, size.height);
    fill.close();
    canvas.drawPath(fill, Paint()
      ..shader = const LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter,
          colors: [Color(0x336C8BFF), Color(0x00000000)]).createShader(Offset.zero & size));
    canvas.drawPath(path, Paint()
      ..color = _accent ..style = PaintingStyle.stroke ..strokeWidth = 2.4
      ..strokeJoin = StrokeJoin.round);
  }
  @override
  bool shouldRepaint(covariant _Spark old) => true;
}
