"""Optional ElevenLabs voice output for P.I.X.A.L."""
from __future__ import annotations

import os
from typing import Any


class PixalVoice:
    def __init__(self) -> None:
        self.api_key = os.getenv("PIXAL_API_KEY")
        self.voice_id = os.getenv("PIXAL_VOICE_ID")
        self.model_id = os.getenv("PIXAL_VOICE_MODEL_ID", "eleven_multilingual_v2")
        self.output_format = os.getenv("PIXAL_VOICE_OUTPUT_FORMAT", "mp3_44100_128")
        self._client: Any | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.voice_id)

    def _get_client(self) -> Any:
        if self._client is None:
            if not self.configured:
                raise RuntimeError("P.I.X.A.L. voice is not configured")
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
        return self._client

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")
        stream = self._get_client().text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format,
        )
        if isinstance(stream, bytes):
            return stream
        return b"".join(chunk for chunk in stream if chunk)
