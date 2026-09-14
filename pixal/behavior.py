"""Deterministic behavior selection for P.I.X.A.L."""
from dataclasses import dataclass
from .state import PixalState


@dataclass(frozen=True)
class BehaviorProfile:
    mode: str
    priority: str
    style: str


def derive_behavior(state: PixalState) -> BehaviorProfile:
    state.clamp()
    if state.concern >= 0.65:
        return BehaviorProfile("protective", "safety", "direct and calm")
    if state.frustration >= 0.65:
        return BehaviorProfile("recovery", "stability", "patient and methodical")
    if state.curiosity >= 0.65:
        return BehaviorProfile("exploration", "learning", "inquisitive and precise")
    if state.confidence >= 0.70:
        return BehaviorProfile("focused", "task", "precise and efficient")
    return BehaviorProfile("calm", "balanced", "warm and analytical")
