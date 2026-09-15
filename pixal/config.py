"""Environment-backed configuration for the standalone P.I.X.A.L. service."""
from __future__ import annotations

import os


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_FAST_MODEL") or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    groq_timeout_s = float(os.getenv("PIXAL_GROQ_TIMEOUT_S", "20"))
    groq_enabled = _env_bool("PIXAL_GROQ_ENABLED", True)

    turso_url = os.getenv("PIXAL_TDB_URL")
    turso_token = os.getenv("PIXAL_TAT")

    voice_api_key = os.getenv("PIXAL_API_KEY")
    voice_id = os.getenv("PIXAL_VOICE_ID")
    voice_model_id = os.getenv("PIXAL_VOICE_MODEL_ID", "eleven_multilingual_v2")
    voice_output_format = os.getenv("PIXAL_VOICE_OUTPUT_FORMAT", "mp3_44100_128")

    memory_max_items = int(os.getenv("PIXAL_MEMORY_MAX_ITEMS", "100"))


settings = Settings()
