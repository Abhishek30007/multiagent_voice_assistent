import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_or_create_owner_user
from app.voice.adapters.sip_telephony import LiveKitSIPTelephonyAdapter
from app.voice.adapters.deepgram_stt import DeepgramSTTAdapter
from app.voice.adapters.cartesia_tts import CartesiaTTSAdapter
from app.voice.session.call_session import CallSession
from app.schemas.common import APIResponse

router = APIRouter()
telephony_adapter = LiveKitSIPTelephonyAdapter()
stt_adapter = DeepgramSTTAdapter()
tts_adapter = CartesiaTTSAdapter()

# In-memory registry of active call sessions (isolated per call_id)
_active_sessions: Dict[str, CallSession] = {}


class WebRTCTokenRequest(BaseModel):
    caller_name: Optional[str] = "Browser Tester"
    room_name: Optional[str] = None


class SimulateTurnRequest(BaseModel):
    call_id: Optional[str] = None
    caller_number: Optional[str] = "+15551234567"
    caller_text: str


@router.post("/token", summary="Generate LiveKit WebRTC Token for Browser Testing")
async def generate_webrtc_token(payload: WebRTCTokenRequest):
    """Generates an authorized WebRTC token to connect browser audio directly to LiveKit."""
    room = payload.room_name or f"test_room_{uuid.uuid4().hex[:8]}"
    identity = payload.caller_name or "user"
    token = telephony_adapter.create_token_for_caller(room_name=room, identity=identity)
    return {
        "token": token,
        "room_name": room,
        "ws_url": telephony_adapter.ws_url,
    }


@router.post("/webhook", summary="Telephony SIP Webhook")
async def telephony_webhook(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Receives incoming call event from SIP provider or LiveKit SIP Dispatch."""
    res = await telephony_adapter.handle_incoming_call(payload)
    return res


@router.post("/simulate_turn", response_model=APIResponse[dict], summary="Simulate Phone Call Conversation Turn")
async def simulate_turn(payload: SimulateTurnRequest, db: AsyncSession = Depends(get_db)):
    """Simulate a voice turn for browser-based testing without needing live PSTN connection."""
    user = await get_or_create_owner_user(db)
    call_id = payload.call_id or f"sim_{uuid.uuid4().hex[:8]}"

    if call_id not in _active_sessions:
        session = CallSession(
            call_id=call_id,
            caller_number=payload.caller_number or "+15551234567",
            user_id=user.id,
            stt_adapter=stt_adapter,
            tts_adapter=tts_adapter,
        )
        _active_sessions[call_id] = session

    session = _active_sessions[call_id]
    mock_audio = payload.caller_text.encode("utf-8")
    
    # Process turn
    result = await session.process_caller_audio(mock_audio, db_session=db)

    return APIResponse(
        success=True,
        message="Turn processed",
        data={
            "call_id": call_id,
            "turn_number": session.turn_count,
            "caller_transcript": result["transcript"],
            "response_text": result["response_text"],
            "latency_ms": result["latency_ms"],
            "evidence_used": result["evidence_used"],
        },
    )


@router.post("/end_call", response_model=APIResponse[dict], summary="End Active Call Session")
async def end_call_session(call_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Ends the active call session and writes audit records to database."""
    session = _active_sessions.pop(call_id, None)
    if not session:
        return APIResponse(success=True, message="Session already terminated or not found")

    await session.end_call(db_session=db, status="completed")
    return APIResponse(
        success=True,
        message=f"Call {call_id} successfully terminated and saved in history.",
    )
