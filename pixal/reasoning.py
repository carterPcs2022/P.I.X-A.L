"""Reasoning interface independent of cloud LLM providers.

The default implementation is deterministic and offline. A local-model
adapter can be added later without changing P.I.X.A.L.'s identity layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from .knowledge import KnowledgeVault


@dataclass(frozen=True)
class ReasoningResult:
    text: str
    mode: str
    knowledge_used: int = 0


class ReasoningEngine:
    def __init__(self, knowledge: KnowledgeVault) -> None:
        self.knowledge = knowledge

    def answer(self, prompt: str) -> ReasoningResult:
        matches = self.knowledge.search(prompt, limit=3)
        if matches:
            context = "\n".join(f"{item.title}: {item.content}" for item in matches)
            return ReasoningResult(
                text=f"Local knowledge retrieved:\n{context}",
                mode="offline-knowledge",
                knowledge_used=len(matches),
            )
        return ReasoningResult(
            text="No matching local knowledge was found. A reasoning model may be attached later.",
            mode="offline-no-model",
            knowledge_used=0,
        )
