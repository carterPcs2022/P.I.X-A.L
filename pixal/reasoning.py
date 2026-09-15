"""Provider-independent reasoning boundary for P.I.X.A.L."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .knowledge import KnowledgeVault

logger = logging.getLogger("pixal.reasoning")


@dataclass(frozen=True)
class ReasoningResult:
    text: str
    mode: str
    knowledge_used: int = 0


class ReasoningEngine:
    """Engineering-focused reasoning facade with offline-first fallback."""

    def __init__(self, knowledge: KnowledgeVault, *, api_key: str | None = None, model: str = "openai/gpt-oss-20b", timeout_s: float = 20.0) -> None:
        self.knowledge = knowledge
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self._client: Any | None = None
        self._client_error: str | None = None

    def _get_client(self) -> Any | None:
        if not self.api_key:
            return None
        if self._client is not None:
            return self._client
        if self._client_error:
            return None
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key, timeout=self.timeout_s, max_retries=1)
            return self._client
        except Exception as exc:  # noqa: BLE001
            self._client_error = f"{type(exc).__name__}: {exc}"
            logger.warning("P.I.X.A.L. Groq client unavailable: %s", self._client_error)
            return None

    def _offline(self, prompt: str) -> ReasoningResult:
        matches = self.knowledge.search(prompt, limit=3)
        if matches:
            context = "\n".join(f"{item.title}: {item.content}" for item in matches)
            return ReasoningResult(
                text=f"Local engineering knowledge retrieved:\n{context}",
                mode="offline-knowledge",
                knowledge_used=len(matches),
            )
        return ReasoningResult(
            text="No matching local knowledge was found. P.I.X.A.L. can continue with an attached reasoning model when available.",
            mode="offline-no-model",
        )

    def answer(self, prompt: str) -> ReasoningResult:
        prompt = str(prompt or "").strip()
        if not prompt:
            return ReasoningResult("No input provided.", "offline-empty")

        client = self._get_client()
        matches = self.knowledge.search(prompt, limit=5)
        context = "\n".join(f"- {item.title}: {item.content}" for item in matches)

        if client is None:
            return self._offline(prompt)

        system = (
            "You are P.I.X.A.L., an engineering and physical-systems specialist. "
            "You focus on robotics, mechanical systems, construction, repair, "
            "sensors, actuators, vehicle engineering, prototyping, and practical "
            "validation. Be precise, calm, and safety-first. Do not claim to be "
            "conscious or to have human feelings. Zane has a separate mind; the "
            "Shared Heart is only a coordination layer. Never provide instructions "
            "that bypass safety systems or emergency stops."
        )
        user = prompt
        if context:
            user += f"\n\nRelevant local knowledge:\n{context}"

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.3,
                max_tokens=1024,
            )
            text = completion.choices[0].message.content or ""
            if text.strip():
                return ReasoningResult(text=text.strip(), mode="groq", knowledge_used=len(matches))
        except Exception as exc:  # noqa: BLE001
            logger.warning("P.I.X.A.L. reasoning failed; using offline fallback: %s", exc)

        return self._offline(prompt)
