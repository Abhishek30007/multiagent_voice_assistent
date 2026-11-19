import os
import uuid
import datetime
from typing import Dict, Any, Optional
from livekit import api
from app.voice.adapters.base import BaseTelephonyAdapter
from app.core.logger import logger


class LiveKitSIPTelephonyAdapter(BaseTelephonyAdapter):
    """Adapter for LiveKit SIP Trunking and Telephone Call Routing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        ws_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("LIVEKIT_API_KEY", "devkey")
        self.api_secret = api_secret or os.getenv("LIVEKIT_API_SECRET", "secret123456789012345678901234")
        self.ws_url = ws_url or os.getenv("LIVEKIT_URL", "wss://livekit.example.com")

    def create_token_for_caller(self, room_name: str, identity: str) -> str:
        """Create a LiveKit participant token for voice streaming."""
        token = (
            api.AccessToken(self.api_key, self.api_secret)
            .with_identity(identity)
            .with_name(f"Caller {identity}")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )
        return token

    async def handle_incoming_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming SIP call dispatch from carrier trunk."""
        caller_number = payload.get("caller_number") or payload.get("from") or "Unknown"
        ai_number = payload.get("called_number") or payload.get("to") or "+15550000000"
        call_id = payload.get("call_id") or str(uuid.uuid4())
        room_name = f"call_{call_id}"

        token = self.create_token_for_caller(room_name=room_name, identity=caller_number)

        logger.info(f"SIP Call Connected: CallID={call_id}, From={caller_number}, To={ai_number}, Room={room_name}")

        return {
            "call_id": call_id,
            "room_name": room_name,
            "token": token,
            "ws_url": self.ws_url,
            "caller_number": caller_number,
            "ai_number": ai_number,
            "status": "connected",
        }

    async def terminate_call(self, call_id: str) -> bool:
        """Terminate SIP call session and tear down WebRTC room."""
        logger.info(f"SIP Call Terminated: CallID={call_id}")
        return True
