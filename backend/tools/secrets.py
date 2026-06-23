"""Secret provider — resolves provider API keys.

Phase 8. Keys are never hard-coded in tool specs; tools fetch them at call/build time. The dev
implementation reads environment variables / settings; in production this is backed by AWS
Secrets Manager (same `get` contract).
"""
from __future__ import annotations

import os


class EnvSecretProvider:
    """Implements ISecrets via environment variables (and optional settings fallback)."""

    def __init__(self, settings=None) -> None:
        self._settings = settings

    def get(self, key: str) -> str | None:
        value = os.getenv(key)
        if value:
            return value
        if self._settings is not None:
            return getattr(self._settings, key.lower(), None)
        return None


class AwsSecretsManagerProvider:
    """Production adapter (lazy import boto3). Same `get` contract."""

    def __init__(self, region: str | None = None) -> None:
        import boto3  # type: ignore  # lazy

        self._client = boto3.client("secretsmanager", region_name=region)

    def get(self, key: str) -> str | None:
        resp = self._client.get_secret_value(SecretId=key)
        return resp.get("SecretString")
