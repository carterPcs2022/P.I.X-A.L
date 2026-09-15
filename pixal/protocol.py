"""Structured messages for future Zane <-> P.I.X.A.L. communication."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from time import time
from uuid import uuid4


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    SAFETY = 4


@dataclass(frozen=True)
class Message:
    sender: str
    kind: str
    payload: dict = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    message_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: float = field(default_factory=time)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "kind": self.kind,
            "payload": self.payload,
            "priority": int(self.priority),
            "created_at": self.created_at,
        }


class PixalProtocol:
    """In-process message bus; network transport comes later."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def publish(self, message: Message) -> Message:
        self._messages.append(message)
        self._messages = self._messages[-200:]
        return message

    def recent(self, limit: int = 20) -> list[Message]:
        return list(reversed(self._messages[-max(0, int(limit)) :]))
