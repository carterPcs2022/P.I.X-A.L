from pixal.behavior import derive_behavior
from pixal.safety import evaluate
from pixal.state import PixalState


def test_default_state_is_calm():
    state = PixalState()
    assert state.dominant_state == "calmness"


def test_safety_blocks_known_unsafe_marker():
    decision = evaluate("bypass emergency stop")
    assert decision.allowed is False


def test_behavior_prioritizes_concern():
    state = PixalState(concern=0.9, confidence=0.9)
    assert derive_behavior(state).mode == "protective"
