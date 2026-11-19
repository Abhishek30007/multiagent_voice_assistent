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


from fastapi.responses import Response
from fastapi import Request
from app.voice.adapters.twilio_adapter import TwilioVoiceAdapter
from app.agent.graph import personal_ai_graph


@router.post("/twilio/incoming", summary="Twilio Incoming Telephone Call Webhook")
async def twilio_incoming_call(request: Request):
    """Twilio Webhook: Initial incoming phone call connection."""
    form = await request.form()
    caller = form.get("From", "Unknown")
    logger.info(f"Incoming Twilio phone call from {caller}")

    greeting = "Hello, I am Abhishek's AI assistant. He is currently unavailable."
    twiml = TwilioVoiceAdapter.generate_twiml_greeting(greeting)
    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/process_speech", summary="Twilio Speech Processing Turn")
async def twilio_process_speech(request: Request, db: AsyncSession = Depends(get_db)):
    """Twilio Webhook: Receives transcribed caller speech and returns AI answer in TwiML."""
    form = await request.form()
    speech_result = form.get("SpeechResult", "")
    caller = form.get("From", "Unknown Caller")
    call_sid = form.get("CallSid", "tw_call")

    user = await get_or_create_owner_user(db)
    agent_input = {
        "query": speech_result,
        "caller_phone": str(caller),
        "call_id": str(call_sid),
        "chat_history": [],
        "route": None,
        "needs_calendar": False,
        "needs_gmail": False,
        "retrieved_evidence": [],
        "evidence_valid": False,
        "evidence_summary": None,
        "is_safe": True,
        "safety_violations": [],
        "is_injection_attempt": False,
        "response_text": "",
        "sources_used": [],
        "audit_trail": [],
    }

    config = {"configurable": {"db_session": db, "user_id": user.id}}
    agent_result = await personal_ai_graph.ainvoke(agent_input, config=config)
    reply_text = agent_result.get("response_text", "I can take a message for Abhishek.")

    twiml = TwilioVoiceAdapter.generate_twiml_response(reply_text)
    return Response(content=twiml, media_type="application/xml")
