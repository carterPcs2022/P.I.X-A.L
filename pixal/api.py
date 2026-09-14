"""Minimal standalone P.I.X.A.L. HTTP API."""
from fastapi import FastAPI
from .behavior import derive_behavior
from .safety import evaluate
from .state import PixalState

app = FastAPI(title="P.I.X.A.L.", version="0.1.0")
state = PixalState()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "system": "P.I.X.A.L.", "version": "0.1.0"}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready", "system": "P.I.X.A.L."}


@app.get("/state")
def get_state() -> dict:
    return {"state": state.snapshot(), "behavior": derive_behavior(state).__dict__}


@app.post("/safety/check")
def safety_check(payload: dict) -> dict:
    decision = evaluate(str(payload.get("text", "")))
    return {"allowed": decision.allowed, "reason": decision.reason}
