"""Runtime coordinator for the standalone P.I.X.A.L. software core."""
from __future__ import annotations

import json

from .behavior import derive_behavior
from .config import settings
from .knowledge import KnowledgeVault
from .memory import MemoryStore
from .protocol import Message, PixalProtocol, Priority
from .reasoning import ReasoningEngine
from .safety import evaluate
from .state import PixalState
from .turso_memory import build_memory_store


class PixalRuntime:
    def __init__(self) -> None:
        self.state = PixalState()
        self.memory, self.memory_mode, self.memory_diagnostic = build_memory_store(
            max_items=settings.memory_max_items
        )
        self.protocol = PixalProtocol()
        self.knowledge = KnowledgeVault()
        self._load_builtin_knowledge()
        self.reasoning = ReasoningEngine(
            self.knowledge,
            api_key=settings.groq_api_key if settings.groq_enabled else None,
            model=settings.groq_model,
            timeout_s=settings.groq_timeout_s,
        )

    def _load_builtin_knowledge(self) -> None:
        try:
            self.knowledge.load_json(self.knowledge.root / "core.json")
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            pass

    def diagnostics(self) -> dict:
        return {
            "system": "P.I.X.A.L.",
            "memory": self.memory_mode,
            "memory_diagnostic": self.memory_diagnostic,
            "knowledge_items": len(self.knowledge.items),
            "groq_configured": bool(settings.groq_api_key and settings.groq_enabled),
            "groq_model": settings.groq_model if settings.groq_enabled else None,
            "voice_configured": bool(settings.voice_api_key and settings.voice_id),
            "state": self.state.snapshot(),
        }

    def process(self, text: str) -> dict:
        text = str(text or "").strip()
        decision = evaluate(text)

        if not decision.allowed:
            self.state.concern = max(self.state.concern, 0.9)
            priority = Priority.SAFETY
            reasoning = None
        else:
            self.state.calmness = min(1.0, self.state.calmness + 0.02)
            priority = Priority.NORMAL
            if text:
                self.memory.add(text, importance=0.5)
            reasoning = self.reasoning.answer(text) if text else None

        self.state.clamp()
        self.protocol.publish(
            Message(
                sender="P.I.X.A.L.",
                kind="safety" if not decision.allowed else "observation",
                payload={"text": text, "allowed": decision.allowed},
                priority=priority,
            )
        )

        behavior = derive_behavior(self.state)
        result = {
            "system": "P.I.X.A.L.",
            "allowed": decision.allowed,
            "reason": decision.reason,
            "state": self.state.snapshot(),
            "behavior": behavior.__dict__,
        }
        if reasoning:
            result["reasoning"] = reasoning.__dict__
        return result

    def close(self) -> None:
        closer = getattr(self.memory, "close", None)
        if closer:
            closer()
