"""Runtime coordinator for the standalone P.I.X.A.L. software core."""
from __future__ import annotations

import json

from .behavior import derive_behavior
from .knowledge import KnowledgeVault
from .memory import MemoryStore
from .protocol import Message, PixalProtocol, Priority
from .reasoning import ReasoningEngine
from .safety import evaluate
from .state import PixalState


class PixalRuntime:
    def __init__(self) -> None:
        self.state = PixalState()
        self.memory = MemoryStore(max_items=100)
        self.protocol = PixalProtocol()
        self.knowledge = KnowledgeVault()
        self._load_builtin_knowledge()
        self.reasoning = ReasoningEngine(self.knowledge)

    def _load_builtin_knowledge(self) -> None:
        try:
            self.knowledge.load_json(self.knowledge.root / "core.json")
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            # The runtime remains usable even if optional knowledge is absent.
            pass

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
