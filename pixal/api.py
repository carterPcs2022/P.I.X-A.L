"""Standalone P.I.X.A.L. HTTP API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from .behavior import derive_behavior
from .runtime import PixalRuntime


runtime = PixalRuntime()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    runtime.close()


app = FastAPI(
    title="P.I.X.A.L.",
    version="0.2.0",
    description="Standalone engineering-focused P.I.X.A.L. service.",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict:
    return {
        "system": "P.I.X.A.L.",
        "status": "online",
        "version": "0.2.0",
        "endpoints": ["/health", "/ready", "/diagnostics", "/state", "/process"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "system": "P.I.X.A.L.", "version": "0.2.0"}


@app.head("/health")
def health_head() -> None:
    return None


@app.get("/ready")
def ready() -> dict:
    diagnostics = runtime.diagnostics()
    return {
        "status": "ready",
        "system": "P.I.X.A.L.",
        "memory": diagnostics["memory"],
        "knowledge": diagnostics["knowledge_items"],
    }


@app.get("/diagnostics")
def diagnostics() -> dict:
    return runtime.diagnostics()


@app.get("/state")
def get_state() -> dict:
    return {"state": runtime.state.snapshot(), "behavior": derive_behavior(runtime.state).__dict__}


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


@app.get("/memory/search")
def search_memory(q: str, limit: int = 5) -> dict:
    return {"items": [item.__dict__ for item in runtime.memory.search(q, limit)]}


@app.get("/protocol/recent")
def recent_protocol(limit: int = 20) -> dict:
    return {"messages": [message.to_dict() for message in runtime.protocol.recent(limit)]}
