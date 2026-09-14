"""Bounded software state for P.I.X.A.L.

These values describe internal software state; they are not claims of human
consciousness or human emotions.
"""
from dataclasses import dataclass, asdict


@dataclass
class PixalState:
    curiosity: float = 0.5
    confidence: float = 0.5
    concern: float = 0.0
    frustration: float = 0.0
    calmness: float = 0.8
    trust: float = 0.5

    def clamp(self) -> None:
        for name in asdict(self):
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))

    @property
    def dominant_state(self) -> str:
        self.clamp()
        values = {
            "concern": self.concern,
            "frustration": self.frustration,
            "curiosity": self.curiosity,
            "confidence": self.confidence,
            "calmness": self.calmness,
        }
        return max(values, key=values.get)

    def snapshot(self) -> dict:
        self.clamp()
        return {**asdict(self), "dominant_state": self.dominant_state}
