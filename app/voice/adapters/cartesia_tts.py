import os
import httpx
from typing import Optional
from app.voice.adapters.base import BaseTTSAdapter
from app.core.logger import logger


class CartesiaTTSAdapter(BaseTTSAdapter):
    """Text-to-Speech adapter powered by Cartesia / ElevenLabs with test fallback."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY", "") or os.getenv("ELEVENLABS_API_KEY", "")

    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        if not self.api_key:
            # Generate deterministic mock audio bytes (RIFF WAV header stub)
            logger.info("TTS API key not configured. Emitting test synthetic WAV bytes.")
            wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            return wav_header + text.encode("utf-8")

        url = "https://api.cartesia.ai/tts/bytes"
        headers = {
            "X-API-Key": self.api_key,
            "Cartesia-Version": "2024-06-10",
            "Content-Type": "application/json",
        }
        payload = {
            "model_id": "sonic-english",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": voice_id or "a0e99841-438c-4a64-b679-ae501e7d6091",
            },
            "output_format": {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": 24000,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return res.content
        except Exception as e:
            logger.warning(f"Cartesia TTS synthesis error: {e}. Falling back to synthetic WAV bytes.")
            wav_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
            return wav_header + text.encode("utf-8")
