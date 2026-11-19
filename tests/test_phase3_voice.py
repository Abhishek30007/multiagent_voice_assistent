import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.call_log import CallLog
from app.voice.adapters.deepgram_stt import DeepgramSTTAdapter
from app.voice.adapters.cartesia_tts import CartesiaTTSAdapter
from app.voice.adapters.sip_telephony import LiveKitSIPTelephonyAdapter
from app.voice.session.call_session import CallSession


@pytest.mark.asyncio
async def test_livekit_token_generation():
    adapter = LiveKitSIPTelephonyAdapter(api_key="test_key", api_secret="test_secret_123456789012345678901234")
    token = adapter.create_token_for_caller(room_name="room_abc", identity="+15551234567")
    assert token is not None
    assert len(token) > 20


@pytest.mark.asyncio
async def test_stt_and_tts_adapters():
    stt = DeepgramSTTAdapter()
    transcript = await stt.transcribe(b"fake audio bytes")
    assert transcript is not None

    tts = CartesiaTTSAdapter()
    audio_bytes = await tts.synthesize("Hello world")
    assert audio_bytes.startswith(b"RIFF")


@pytest.mark.asyncio
async def test_call_session_isolation(db_session: AsyncSession, test_owner: User):
    stt = DeepgramSTTAdapter()
    tts = CartesiaTTSAdapter()

    # Session 1
    session1 = CallSession(
        call_id="call_001",
        caller_number="+15551111111",
        user_id=test_owner.id,
        stt_adapter=stt,
        tts_adapter=tts,
    )
    # Session 2
    session2 = CallSession(
        call_id="call_002",
        caller_number="+15552222222",
        user_id=test_owner.id,
        stt_adapter=stt,
        tts_adapter=tts,
    )

    turn1 = await session1.process_caller_audio(b"Audio 1", db_session=db_session)
    turn2 = await session2.process_caller_audio(b"Audio 2", db_session=db_session)

    assert session1.call_id != session2.call_id
    assert session1.caller_number != session2.caller_number
    assert len(session1.chat_history) == 2  # user + assistant
    assert len(session2.chat_history) == 2

    # Verify sessions end and log into database separately
    await session1.end_call(db_session=db_session, status="completed")
    await session2.end_call(db_session=db_session, status="completed")

    res = await db_session.execute(select(CallLog).where(CallLog.user_id == test_owner.id))
    logs = res.scalars().all()
    assert len(logs) == 2


@pytest.mark.asyncio
async def test_voice_endpoints(client: AsyncClient, test_owner: User):
    # 1. Token generation endpoint
    res_tok = await client.post("/api/v1/voice/token", json={"caller_name": "TestUser"})
    assert res_tok.status_code == 200
    assert "token" in res_tok.json()

    # 2. Simulate voice call turn
    sim_payload = {
        "call_id": "test_sim_call_99",
        "caller_number": "+15553334444",
        "caller_text": "Is Abhishek free tomorrow?",
    }
    res_sim = await client.post("/api/v1/voice/simulate_turn", json=sim_payload)
    assert res_sim.status_code == 200
    data = res_sim.json()["data"]
    assert data["call_id"] == "test_sim_call_99"
    assert "response_text" in data

    # 3. End call
    res_end = await client.post("/api/v1/voice/end_call?call_id=test_sim_call_99")
    assert res_end.status_code == 200

    # 4. Check Call History endpoint
    res_hist = await client.get("/api/v1/calls/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["total"] >= 1
