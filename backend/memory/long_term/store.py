"""Long-term store implementations (the ILongTermStore port).

Phase 7. In-memory record store (default) and a PostgreSQL adapter (production) using SQLAlchemy
Core with a single ``memories`` table.
"""
from __future__ import annotations

from backend.memory.record import MemoryRecord


class InMemoryLongTermStore:
    """Default structured store; no external dependency."""

    def __init__(self) -> None:
        self._rows: dict[str, MemoryRecord] = {}

    def insert(self, rec: MemoryRecord) -> None:
        self._rows[rec.id] = rec

    def get(self, mid: str) -> MemoryRecord | None:
        return self._rows.get(mid)

    def delete(self, mid: str) -> None:
        self._rows.pop(mid, None)

    def hydrate(self, ids: list[str]) -> list[MemoryRecord]:
        return [self._rows[i] for i in ids if i in self._rows]

    def query(self, scope: str, owner: str, limit: int = 50) -> list[MemoryRecord]:
        rows = [r for r in self._rows.values() if r.scope == scope and r.owner == owner]
        rows.sort(key=lambda r: r.ts, reverse=True)
        return rows[:limit]


class PostgresLongTermStore:
    """Production adapter backed by PostgreSQL (lazy import; SQLAlchemy Core, sync engine)."""

    def __init__(self, dsn: str) -> None:
        from sqlalchemy import (Column, DateTime, MetaData, String, Table,  # type: ignore
                                Text, create_engine)
        from sqlalchemy.dialects.postgresql import JSONB  # type: ignore

        self._engine = create_engine(dsn, future=True)
        self._meta = MetaData()
        self._t = Table(
            "memories", self._meta,
            Column("id", String, primary_key=True),
            Column("scope", String, index=True),
            Column("owner", String, index=True),
            Column("kind", String),
            Column("content", Text),
            Column("metadata", JSONB),
            Column("ts", DateTime(timezone=True)),
        )
        self._meta.create_all(self._engine)

    def _row_to_record(self, row) -> MemoryRecord:
        return MemoryRecord(id=row.id, scope=row.scope, owner=row.owner, kind=row.kind,
                            content=row.content, metadata=row.metadata or {}, ts=row.ts)

    def insert(self, rec: MemoryRecord) -> None:
        from sqlalchemy import insert  # type: ignore
        with self._engine.begin() as conn:
            conn.execute(insert(self._t).values(
                id=rec.id, scope=rec.scope, owner=rec.owner, kind=rec.kind,
                content=rec.content, metadata=rec.metadata, ts=rec.ts))

    def get(self, mid: str) -> MemoryRecord | None:
        from sqlalchemy import select  # type: ignore
        with self._engine.begin() as conn:
            row = conn.execute(select(self._t).where(self._t.c.id == mid)).first()
        return self._row_to_record(row) if row else None

    def delete(self, mid: str) -> None:
        from sqlalchemy import delete  # type: ignore
        with self._engine.begin() as conn:
            conn.execute(delete(self._t).where(self._t.c.id == mid))

    def hydrate(self, ids: list[str]) -> list[MemoryRecord]:
        from sqlalchemy import select  # type: ignore
        if not ids:
            return []
        with self._engine.begin() as conn:
            rows = conn.execute(select(self._t).where(self._t.c.id.in_(ids))).all()
        by_id = {r.id: self._row_to_record(r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]  # preserve ranking order

    def query(self, scope: str, owner: str, limit: int = 50) -> list[MemoryRecord]:
        from sqlalchemy import select  # type: ignore
        with self._engine.begin() as conn:
            rows = conn.execute(
                select(self._t)
                .where(self._t.c.scope == scope, self._t.c.owner == owner)
                .order_by(self._t.c.ts.desc()).limit(limit)).all()
        return [self._row_to_record(r) for r in rows]
