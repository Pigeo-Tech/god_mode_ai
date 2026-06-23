"""Permission Manager — RBAC, deny-by-default, fully audited.

Phase 2. Implements the IPermissionManager port. Principals (users or agents) are assigned
roles; roles grant scopes. A scope may use a trailing wildcard (e.g. ``tool:*``). Every
authorization decision is written to the audit trail.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


class PermissionError(Exception):
    """Raised when a principal lacks a required scope."""


@dataclass
class AuditEntry:
    principal: str
    scope: str
    decision: str  # "allow" | "deny"
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PermissionManager:
    """Implements the IPermissionManager port."""

    def __init__(self, logger=None) -> None:
        self._role_scopes: dict[str, set[str]] = {}
        self._principal_roles: dict[str, set[str]] = {}
        self._audit: list[AuditEntry] = []
        self._log = logger

    # ---- administration ----
    def grant(self, role: str, scope: str) -> None:
        self._role_scopes.setdefault(role, set()).add(scope)

    def revoke(self, role: str, scope: str) -> None:
        self._role_scopes.get(role, set()).discard(scope)

    def assign(self, principal: str, role: str) -> None:
        self._principal_roles.setdefault(principal, set()).add(role)

    def unassign(self, principal: str, role: str) -> None:
        self._principal_roles.get(principal, set()).discard(role)

    def scopes_for(self, principal: str) -> set[str]:
        scopes: set[str] = set()
        for role in self._principal_roles.get(principal, set()):
            scopes |= self._role_scopes.get(role, set())
        return scopes

    # ---- decisions ----
    @staticmethod
    def _matches(granted: str, requested: str) -> bool:
        if granted == "*" or granted == requested:
            return True
        if granted.endswith(":*"):
            return requested.startswith(granted[:-1])  # keep the colon
        return False

    async def check(self, principal: str, scope: str) -> bool:
        allowed = any(self._matches(g, scope) for g in self.scopes_for(principal))
        self._record(principal, scope, "allow" if allowed else "deny")
        return allowed

    async def require(self, principal: str, scope: str) -> None:
        if not await self.check(principal, scope):
            raise PermissionError(f"{principal} lacks scope {scope!r}")

    def _record(self, principal: str, scope: str, decision: str) -> None:
        self._audit.append(AuditEntry(principal, scope, decision))
        if self._log:
            self._log.info("authz.decision", principal=principal, scope=scope, decision=decision)

    @property
    def audit_log(self) -> list[AuditEntry]:
        return list(self._audit)
