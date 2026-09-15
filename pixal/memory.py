"""Small bounded memory store for P.I.X.A.L.

This is intentionally local and dependency-free. Durable storage can be
plugged in later without changing the public memory interface.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from time import time
from typing import Iterable


@dataclass
class MemoryItem:
    text: str
    importance: float = 0.5
    created_at: float = 0.0

    def __post_init__(self) -> None:
        self.importance = max(0.0, min(1.0, float(self.importance)))
        if not self.created_at:
            self.created_at = time()


class MemoryStore:
    """Bounded memory with simple recency/importance retrieval."""

    def __init__(self, max_items: int = 100) -> None:
        self.max_items = max(1, int(max_items))
        self._items: list[MemoryItem] = []

    def add(self, text: str, importance: float = 0.5) -> MemoryItem:
        item = MemoryItem(str(text), importance)
        self._items.append(item)
        self._items = self._items[-self.max_items :]
        return item

    def recent(self, limit: int = 10) -> list[MemoryItem]:
        return list(reversed(self._items[-max(0, int(limit)) :]))

    def search(self, query: str, limit: int = 5) -> list[MemoryItem]:
        terms = {part.lower() for part in str(query).split() if part.strip()}
        if not terms:
            return self.recent(limit)

        now = time()
        scored: list[tuple[float, MemoryItem]] = []
        for item in self._items:
            words = set(item.text.lower().split())
            overlap = len(terms & words) / len(terms)
            age = max(0.0, now - item.created_at)
            recency = 1.0 / (1.0 + age / 3600.0)
            score = overlap * 0.65 + item.importance * 0.25 + recency * 0.10
            if overlap > 0:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[: max(0, int(limit))]]

    def serialize(self) -> list[dict]:
        return [asdict(item) for item in self._items]

    def load(self, items: Iterable[dict]) -> None:
        self._items = [MemoryItem(**item) for item in items][-self.max_items :]
