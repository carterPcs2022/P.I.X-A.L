"""Standalone P.I.X.A.L. HTTP API."""
from contextlib import asynccontextmanager
import base64

from fastapi import FastAPI, HTTPException
from .behavior import derive_behavior
from .runtime import PixalRuntime
from .voice import PixalVoice


runtime = PixalRuntime()
voice = PixalVoice()


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
        "endpoints": ["/health", "/ready", "/diagnostics", "/state", "/process", "/speak"],
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
        "voice": diagnostics["voice_configured"],
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


@app.post("/speak")
def speak(payload: dict) -> dict:
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if not voice.configured:
        raise HTTPException(status_code=503, detail="P.I.X.A.L. voice is not configured")
    try:
        audio = voice.synthesize(text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Voice synthesis failed") from exc
    if not audio:
        raise HTTPException(status_code=502, detail="Voice synthesis returned no audio")
    return {
        "system": "P.I.X.A.L.",
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "audio_format": voice.output_format,
    }


@app.get("/memory/recent")
def recent_memory(limit: int = 10) -> dict:
    return {"items": [item.__dict__ for item in runtime.memory.recent(limit)]}


@app.get("/memory/search")
def search_memory(q: str, limit: int = 5) -> dict:
    return {"items": [item.__dict__ for item in runtime.memory.search(q, limit)]}


@app.get("/protocol/recent")
def recent_protocol(limit: int = 20) -> dict:
    return {"messages": [message.to_dict() for message in runtime.protocol.recent(limit)]}
