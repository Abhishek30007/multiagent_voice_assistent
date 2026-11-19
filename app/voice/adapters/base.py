from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator


class BaseSTTAdapter(ABC):
    """Abstract interface for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes, mime_type: str = "audio/wav") -> str:
        """Convert caller audio into text."""
        pass


class BaseTTSAdapter(ABC):
    """Abstract interface for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Convert agent response text into audio bytes."""
        pass


class BaseTelephonyAdapter(ABC):
    """Abstract interface for SIP / PSTN telephony trunking."""

    @abstractmethod
    async def handle_incoming_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming call webhook from telephony trunk."""
        pass

    @abstractmethod
    async def terminate_call(self, call_id: str) -> bool:
        """Hang up or terminate call session."""
        pass
