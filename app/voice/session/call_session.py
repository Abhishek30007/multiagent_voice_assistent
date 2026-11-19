import datetime
import json
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agent.graph import personal_ai_graph
from app.models.call_log import CallLog
from app.voice.adapters.deepgram_stt import DeepgramSTTAdapter
from app.voice.adapters.cartesia_tts import CartesiaTTSAdapter
from app.core.logger import logger


class CallSession:
    """Manages an individual phone call's lifecycle, turn-taking, and state isolation."""

    def __init__(
        self,
        call_id: str,
        caller_number: str,
        user_id: int,
        stt_adapter: DeepgramSTTAdapter,
        tts_adapter: CartesiaTTSAdapter,
    ):
        self.call_id = call_id
        self.caller_number = caller_number
        self.user_id = user_id
        self.stt_adapter = stt_adapter
        self.tts_adapter = tts_adapter

        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.turn_count = 0
        self.chat_history: List[Dict[str, str]] = []
        self.evidence_sources: List[Dict[str, str]] = []
        self.is_active = True
        self.status = "connected"

    async def get_greeting(self) -> str:
        """Standard introductory greeting as an AI assistant."""
        greeting = "Hello, I'm Abhishek's AI assistant. He is currently unavailable. How may I help you?"
        self.chat_history.append({"role": "assistant", "content": greeting})
        return greeting

    async def process_caller_audio(self, audio_bytes: bytes, db_session: AsyncSession) -> Dict[str, Any]:
        """Convert incoming caller audio to text, execute LangGraph agent, and synthesize speech."""
        self.turn_count += 1
        t0 = datetime.datetime.now()

        # 1. Speech-to-Text
        transcript = await self.stt_adapter.transcribe(audio_bytes)
        logger.info(f"[{self.call_id}] Caller Turn {self.turn_count}: '{transcript}'")
        self.chat_history.append({"role": "user", "content": transcript})

        # 2. Invoke LangGraph multi-agent workflow
        agent_input = {
            "query": transcript,
            "caller_phone": self.caller_number,
            "call_id": self.call_id,
            "chat_history": self.chat_history,
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

        config = {
            "configurable": {
                "db_session": db_session,
                "user_id": self.user_id,
            }
        }
        agent_result = await personal_ai_graph.ainvoke(agent_input, config=config)

        response_text = agent_result.get("response_text", "I'm sorry, I encountered a brief issue. Could you repeat that?")
        self.chat_history.append({"role": "assistant", "content": response_text})

        # Record used sources
        for s in agent_result.get("sources_used", []):
            if s not in self.evidence_sources:
                self.evidence_sources.append(s)

        # 3. Text-to-Speech
        audio_response = await self.tts_adapter.synthesize(response_text)

        t1 = datetime.datetime.now()
        latency_ms = int((t1 - t0).total_seconds() * 1000)

        return {
            "transcript": transcript,
            "response_text": response_text,
            "audio_bytes": audio_response,
            "evidence_used": agent_result.get("sources_used", []),
            "latency_ms": latency_ms,
            "is_safe": agent_result.get("is_safe", True),
        }

    async def end_call(self, db_session: AsyncSession, status: str = "completed"):
        """Save call record and audit information to PostgreSQL upon call wrapup."""
        self.is_active = False
        self.status = status
        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = int((end_time - self.start_time).total_seconds())

        summary = f"Handled {self.turn_count} turn(s). Sources referenced: {len(self.evidence_sources)}"

        call_record = CallLog(
            user_id=self.user_id,
            call_id=self.call_id,
            caller_number=self.caller_number,
            call_start_time=self.start_time,
            call_end_time=end_time,
            duration_seconds=max(duration, 1),
            call_status=self.status,
            turn_count=self.turn_count,
            agent_execution_summary=summary,
            evidence_source_references=json.dumps(self.evidence_sources),
        )
        db_session.add(call_record)
        await db_session.commit()
        logger.info(f"[{self.call_id}] Call ended and logged in PostgreSQL: duration={duration}s, status={self.status}")
