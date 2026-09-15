"""Durable P.I.X.A.L. memory for Render/Turso deployments.

Turso is optional. When PIXAL_TDB_URL and PIXAL_TAT are unavailable or the
remote database cannot be reached, the runtime falls back to its bounded
in-process MemoryStore instead of failing startup.
"""
from __future__ import annotations

import os
import time
from types import SimpleNamespace
from typing import Any, Iterable

import httpx

from .memory import MemoryItem, MemoryStore


_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pixal_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    importance REAL NOT NULL,
    created_at REAL NOT NULL
)
"""


class _TursoClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.replace("libsql://", "https://", 1).rstrip("/") + "/v2/pipeline"
        self.client = httpx.Client(timeout=3.0)
        self.headers = {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _arg(value: Any) -> dict[str, Any]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "integer", "value": str(int(value))}
        if isinstance(value, int):
            return {"type": "integer", "value": str(value)}
        if isinstance(value, float):
            return {"type": "float", "value": value}
        return {"type": "text", "value": str(value)}

    def execute(self, sql: str, args: Iterable[Any] = ()) -> Any:
        payload = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": [self._arg(v) for v in args]}},
                {"type": "close"},
            ]
        }
        response = self.client.post(self.url, json=payload, headers=self.headers)
        response.raise_for_status()
        body = response.json()
        first = body["results"][0]
        if first.get("type") != "ok":
            raise RuntimeError("Turso pipeline request failed")
        rows = []
        for row in first["response"]["result"].get("rows", []):
            rows.append([cell.get("value") if isinstance(cell, dict) else cell for cell in row])
        return SimpleNamespace(rows=rows)

    def close(self) -> None:
        self.client.close()


class TursoMemoryStore(MemoryStore):
    """MemoryStore synchronized with P.I.X.A.L.'s dedicated Turso database."""

    def __init__(self, max_items: int = 100, client: Any | None = None) -> None:
        super().__init__(max_items=max_items)
        if client is None:
            url = os.getenv("PIXAL_TDB_URL")
            token = os.getenv("PIXAL_TAT")
            if not url or not token:
                raise RuntimeError("PIXAL_TDB_URL and PIXAL_TAT are required for Turso memory")
            client = _TursoClient(url, token)
        self._client = client
        self._client.execute(_TABLE_SQL)
        self._load_remote()
        self._trim_remote()

    @staticmethod
    def is_configured() -> bool:
        return bool(os.getenv("PIXAL_TDB_URL") and os.getenv("PIXAL_TAT"))

    def _load_remote(self) -> None:
        result = self._client.execute(
            "SELECT text, importance, created_at FROM pixal_memories ORDER BY created_at ASC"
        )
        self._items = [
            MemoryItem(text=str(row[0]), importance=float(row[1]), created_at=float(row[2]))
            for row in result.rows
        ][-self.max_items :]

    def add(self, text: str, importance: float = 0.5) -> MemoryItem:
        item = super().add(text, importance)
        self._client.execute(
            "INSERT INTO pixal_memories(text, importance, created_at) VALUES (?, ?, ?)",
            (item.text, item.importance, item.created_at),
        )
        self._trim_remote()
        return item

    def _trim_remote(self) -> None:
        self._client.execute(
            "DELETE FROM pixal_memories WHERE memory_id NOT IN "
            "(SELECT memory_id FROM pixal_memories ORDER BY created_at DESC LIMIT ?)",
            (self.max_items,),
        )

    def ping(self) -> float:
        started = time.monotonic()
        self._client.execute("SELECT 1")
        return (time.monotonic() - started) * 1000

    def close(self) -> None:
        closer = getattr(self._client, "close", None)
        if closer:
            closer()


def build_memory_store(max_items: int = 100) -> tuple[MemoryStore, str, str | None]:
    """Return (store, mode, diagnostic) without failing service startup."""
    if TursoMemoryStore.is_configured():
        try:
            return TursoMemoryStore(max_items=max_items), "turso", None
        except Exception as exc:  # noqa: BLE001
            return MemoryStore(max_items=max_items), "local-fallback", f"{type(exc).__name__}: {exc}"
    return MemoryStore(max_items=max_items), "local", None
