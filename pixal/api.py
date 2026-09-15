"""Standalone P.I.X.A.L. HTTP API."""
from fastapi import FastAPI
from .runtime import PixalRuntime

app = FastAPI(title="P.I.X.A.L.", version="0.1.0")
runtime = PixalRuntime()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "system": "P.I.X.A.L.", "version": "0.1.0"}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready", "system": "P.I.X.A.L."}


@app.get("/state")
def get_state() -> dict:
    return {"state": runtime.state.snapshot(), "behavior": runtime.process("")["behavior"]}


@app.post("/process")
def process(payload: dict) -> dict:
    return runtime.process(str(payload.get("text", "")))


@app.post("/safety/check")
def safety_check(payload: dict) -> dict:
    result = runtime.process(str(payload.get("text", "")))
    return {"allowed": result["allowed"], "reason": result["reason"]}


@app.get("/memory/recent")
def recent_memory(limit: int = 10) -> dict:
    return {"items": [item.__dict__ for item in runtime.memory.recent(limit)]}


@app.get("/protocol/recent")
def recent_protocol(limit: int = 20) -> dict:
    return {"messages": [message.to_dict() for message in runtime.protocol.recent(limit)]}
