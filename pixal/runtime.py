"""Runtime coordinator for the standalone P.I.X.A.L. software core."""
from __future__ import annotations

from .behavior import derive_behavior
from .memory import MemoryStore
from .protocol import Message, PixalProtocol, Priority
from .safety import evaluate
from .state import PixalState


class PixalRuntime:
    def __init__(self) -> None:
        self.state = PixalState()
        self.memory = MemoryStore(max_items=100)
        self.protocol = PixalProtocol()

    def process(self, text: str) -> dict:
        text = str(text or "").strip()
        decision = evaluate(text)

        if not decision.allowed:
            self.state.concern = max(self.state.concern, 0.9)
            priority = Priority.SAFETY
        else:
            self.state.calmness = min(1.0, self.state.calmness + 0.02)
            priority = Priority.NORMAL
            if text:
                self.memory.add(text, importance=0.5)

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
        return {
            "system": "P.I.X.A.L.",
            "allowed": decision.allowed,
            "reason": decision.reason,
            "state": self.state.snapshot(),
            "behavior": behavior.__dict__,
        }
