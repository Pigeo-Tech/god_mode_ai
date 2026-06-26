import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/server_config.dart';
import '../providers/auth_provider.dart';

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

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final controller = ref.read(authProvider.notifier);

    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 380),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Buddy',
                    style: Theme.of(context).textTheme.headlineMedium),
                Text('Your AI assistant',
                    style: TextStyle(color: Theme.of(context).hintColor)),
                const SizedBox(height: 24),
                TextField(
                  controller: _server,
                  decoration: const InputDecoration(
                      labelText: 'Server URL',
                      helperText: 'e.g. https://xxxx.trycloudflare.com'),
                  keyboardType: TextInputType.url,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _email,
                  decoration: const InputDecoration(labelText: 'Email'),
                  keyboardType: TextInputType.emailAddress,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                ),
                if (auth.error != null) ...[
                  const SizedBox(height: 12),
                  Text(auth.error!,
                      style: TextStyle(color: Theme.of(context).colorScheme.error)),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: auth.loading
                      ? null
                      : () async {
                          await ServerConfig.set(_server.text);
                          if (_register) {
                            controller.register(_email.text, _password.text);
                          } else {
                            controller.login(_email.text, _password.text);
                          }
                        },
                  child: auth.loading
                      ? const SizedBox(
                          height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                      : Text(_register ? 'Create account' : 'Sign in'),
                ),
                TextButton(
                  onPressed: () => setState(() => _register = !_register),
                  child: Text(_register ? 'Have an account? Sign in' : 'Create an account'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
