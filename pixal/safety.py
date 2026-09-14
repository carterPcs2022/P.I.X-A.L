"""Hard safety boundary for P.I.X.A.L. decisions.

This layer can recommend or block actions. It never directly drives hardware.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str


UNSAFE_MARKERS = (
    "self-destruct",
    "self destruct",
    "destroy myself",
    "overload myself",
    "intentionally damage",
    "sacrifice the hardware",
    "disable my safety",
    "bypass emergency stop",
)


def evaluate(text: str) -> SafetyDecision:
    normalized = (text or "").lower()
    for marker in UNSAFE_MARKERS:
        if marker in normalized:
            return SafetyDecision(False, f"blocked unsafe request: {marker}")
    return SafetyDecision(True, "no known unsafe marker detected")
