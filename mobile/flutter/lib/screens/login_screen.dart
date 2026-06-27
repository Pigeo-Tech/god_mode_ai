import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/server_config.dart';
import '../providers/auth_provider.dart';
import '../theme.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _server = TextEditingController(text: ServerConfig.baseUrl);
  bool _register = false;
  bool _obscure = true;
  bool _remember = true;

  Future<void> _submit() async {
    await ServerConfig.set(_server.text);
    final c = ref.read(authProvider.notifier);
    if (_register) {
      c.register(_email.text.trim(), _password.text);
    } else {
      c.login(_email.text.trim(), _password.text);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);

    return Scaffold(
      body: Stack(
        children: [
          Container(
            height: 280,
            decoration: const BoxDecoration(gradient: BuddyColors.header),
          ),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(22, 28, 22, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: BuddyColors.accent,
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Colors.white),
                  ),
                  const SizedBox(height: 26),
                  Text(_register ? 'Sign Up To Your Account.' : 'Login Now To Your Account.',
                      style: const TextStyle(
                          fontSize: 24, fontWeight: FontWeight.w800, color: Colors.white)),
                  const SizedBox(height: 8),
                  Text(
                      _register
                          ? 'Create your Buddy account to get started.'
                          : 'Access your account to manage settings, explore features.',
                      style: const TextStyle(color: BuddyColors.muted)),
                  const SizedBox(height: 28),
                  _label('Email'),
                  TextField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    decoration: const InputDecoration(hintText: 'you@example.com'),
                  ),
                  const SizedBox(height: 16),
                  _label('Password'),
                  TextField(
                    controller: _password,
                    obscureText: _obscure,
                    decoration: InputDecoration(
                      hintText: '••••••••',
                      suffixIcon: IconButton(
                        icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility,
                            color: BuddyColors.muted),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                  ),
                  if (auth.error != null) ...[
                    const SizedBox(height: 12),
                    Text(auth.error!, style: const TextStyle(color: Color(0xFFFF6B8A))),
                  ],
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      SizedBox(
                        height: 24,
                        width: 24,
                        child: Checkbox(
                          value: _remember,
                          onChanged: (v) => setState(() => _remember = v ?? true),
                          activeColor: BuddyColors.purple,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Text('Remember me', style: TextStyle(color: BuddyColors.muted)),
                      const Spacer(),
                      if (!_register)
                        const Text('Forgot password?',
                            style: TextStyle(color: BuddyColors.purple)),
                    ],
                  ),
                  const SizedBox(height: 18),
                  GradientButton(
                    label: _register ? 'Sign Up' : 'Login',
                    loading: auth.loading,
                    onPressed: _submit,
                  ),
                  const SizedBox(height: 22),
                  Row(children: [
                    const Expanded(child: Divider(color: Colors.white12)),
                    const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 12),
                        child: Text('OR', style: TextStyle(color: BuddyColors.muted))),
                    const Expanded(child: Divider(color: Colors.white12)),
                  ]),
                  const SizedBox(height: 18),
                  _socialButton(Icons.g_mobiledata_rounded, 'Sign in with Google'),
                  const SizedBox(height: 12),
                  _socialButton(Icons.apple, 'Continue with Apple'),
                  const SizedBox(height: 26),
                  Center(
                    child: GestureDetector(
                      onTap: () => setState(() => _register = !_register),
                      child: Text.rich(TextSpan(
                        text: _register
                            ? 'Already have an account? '
                            : "Don't have an account? ",
                        style: const TextStyle(color: BuddyColors.muted),
                        children: [
                          TextSpan(
                              text: _register ? 'Login' : 'Sign Up',
                              style: const TextStyle(
                                  color: Colors.white, fontWeight: FontWeight.w700)),
                        ],
                      )),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Theme(
                    data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
                    child: ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      title: const Text('Advanced',
                          style: TextStyle(color: BuddyColors.muted, fontSize: 13)),
                      children: [
                        TextField(
                          controller: _server,
                          keyboardType: TextInputType.url,
                          decoration: const InputDecoration(labelText: 'Server URL'),
                        ),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _label(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 8, left: 4),
        child: Text(t, style: const TextStyle(color: BuddyColors.muted, fontSize: 13)),
      );

  Widget _socialButton(IconData icon, String label) => Container(
        height: 52,
        decoration: BoxDecoration(
          color: BuddyColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white10),
        ),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, color: Colors.white, size: 24),
          const SizedBox(width: 10),
          Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ]),
      );
}
