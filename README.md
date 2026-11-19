# Personal AI Twin – Real-Time AI Phone Representative

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![LiveKit](https://img.shields.io/badge/LiveKit-Voice%20Agents-0052CC.svg)](https://livekit.io/)
[![Deepgram](https://img.shields.io/badge/Deepgram-STT-13EF95.svg)](https://deepgram.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)

An autonomous personal AI telephone representative for **Abhishek**. When someone calls Abhishek's dedicated AI phone number, the assistant receives the incoming call, introduces itself as an AI assistant, transcribes the caller's speech in real-time, queries an integrated LangGraph multi-agent system grounded strictly in Abhishek's connected Gmail and primary Google Calendar records, and replies with natural speech.

---

## 1. System Architecture

```
Incoming Telephone Call
        │
        ▼
Telephony Provider (Twilio / Telnyx / Carrier)
        │
        ▼
LiveKit SIP Trunking
        │
        ▼
LiveKit Voice Session Manager
        │
        ▼
Deepgram Speech-to-Text Adapter
        │
        ▼
LangGraph Multi-Agent Engine
 ├── Supervisor Agent (Intent classification & prompt injection filter)
 ├── Gmail Retrieval Agent (Grounded email record extraction)
 ├── Calendar Agent (Schedule conflict & free/busy solver)
 ├── Evidence Validation Agent (Anti-hallucination verification)
 ├── Safety & Policy Agent (Privacy disclosure rules & write-action blocker)
 └── Response Generation Agent (Voice-optimized persona formulator)
        │
        ▼
Cartesia / ElevenLabs Text-to-Speech Adapter
        │
        ▼
Caller Hears Grounded AI Response
```

---

## 2. Completed Features

### Phase 1: Data Ingestion & Storage
- **Google OAuth 2.0**: Secure read-only authorization flow with 256-bit Fernet encryption of stored tokens.
- **Gmail Ingestion**: MIME parsing, text & HTML extraction, category classification, and incremental history sync.
- **Google Calendar Ingestion**: SyncToken-based incremental updates, timezone normalization to UTC, free/busy querying.
- **PostgreSQL 16 & Redis 7**: Strict relational schemas for users, encrypted tokens, emails, calendar events, and call logs with distributed concurrency locking.
- **Celery Workers & Beat**: Automated background synchronization every 15 minutes.

### Phase 2: LangGraph Multi-Agent Architecture
- **Supervisor Agent**: Classifies caller intent, detects adversarial jailbreaks, and orchestrates specialized retrieval agents.
- **Gmail & Calendar Retrieval Agents**: Extracts personal facts directly from PostgreSQL.
- **Evidence Validation Agent**: Enforces strict grounding against stored records. Abstains on unverified queries (*"I don't have verified information about that. I can take a message for him."*).
- **Safety & Policy Agent**: Filters out credentials, bank details, and OTPs. Prohibits making commitments or modifying events.
- **Response Agent**: Formulates concise, natural, polite spoken answers without impersonating Abhishek.

### Phase 3: Voice Calling, Observability & Dashboard
- **LiveKit Agents & SIP Telephony**: Full telephone trunking, session isolation per call, interruption handling, and browser-based WebRTC testing.
- **Provider Adapters**: Pluggable interfaces for STT (Deepgram), TTS (Cartesia / ElevenLabs), and Telephony (LiveKit SIP).
- **OpenTelemetry & Metrics**: Tracks call latency, STT latency, agent execution time, time-to-first-spoken-response, and token costs.
- **React + TypeScript Dashboard**:
  - **Overview**: Real-time sync status, email/calendar counts, and voice representative health.
  - **Emails**: Filterable by category (`Assessment`, `Interview`, `Career`, etc.) with keyword search.
  - **Calendar**: Today's and upcoming events with location and timing details.
  - **Call History**: Call logs with duration, turn count, execution summary, and source references.
  - **Agent Monitor**: Live latency breakdown, token consumption, and error rates.
  - **Settings**: Google account connection, phone trunk settings, and privacy controls.
  - **Interactive Voice Tester**: In-browser simulator to test telephone calls immediately.

---

## 3. Directory Structure

```
multiagent_voice_assistent/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── README.md
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial_phase1_schema.py
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── logger.py
│   │   ├── redis_client.py
│   │   ├── security.py
│   │   └── telemetry.py
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── email.py
│   │   ├── calendar.py
│   │   ├── sync_state.py
│   │   └── call_log.py
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes/
│   │   │   ├── supervisor.py
│   │   │   ├── gmail_agent.py
│   │   │   ├── calendar_agent.py
│   │   │   ├── evidence_validator.py
│   │   │   ├── safety_agent.py
│   │   │   └── response_agent.py
│   │   └── tools/
│   │       └── retrieval_tools.py
│   ├── voice/
│   │   ├── adapters/
│   │   │   ├── base.py
│   │   │   ├── deepgram_stt.py
│   │   │   ├── cartesia_tts.py
│   │   │   └── sip_telephony.py
│   │   └── session/
│   │       └── call_session.py
│   └── api/
│       └── v1/
│           ├── router.py
│           └── endpoints/
│               ├── auth.py
│               ├── emails.py
│               ├── calendar.py
│               ├── sync.py
│               ├── agent.py
│               ├── voice.py
│               ├── calls.py
│               ├── metrics.py
│               └── health.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── pages/
│       │   ├── OverviewPage.tsx
│       │   ├── EmailsPage.tsx
│       │   ├── CalendarPage.tsx
│       │   ├── CallHistoryPage.tsx
│       │   ├── AgentMonitorPage.tsx
│       │   └── SettingsPage.tsx
│       └── components/
│           └── VoiceTesterModal.tsx
├── docs/
│   ├── ARCHITECTURE.md
│   └── GCP_DEPLOYMENT.md
└── tests/
    ├── conftest.py
    ├── test_crypto.py
    ├── test_email_ingestion.py
    ├── test_calendar_ingestion.py
    ├── test_auth.py
    ├── test_api_endpoints.py
    ├── test_sync_manager.py
    ├── test_phase2_agents.py
    ├── test_phase3_voice.py
    ├── test_phase3_telemetry.py
    └── test_e2e_scenarios.py
```

---

## 4. How to Run the Application

### Option A: Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the FastAPI backend**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Start the React frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

---

### Option B: Docker Compose (Full Stack)

Run the entire stack (PostgreSQL, Redis, FastAPI Backend, Celery Worker, Celery Beat, and React Frontend) with one command:

```bash
docker-compose up --build
```

- Dashboard: [http://localhost:3000](http://localhost:3000)
- Backend Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 5. Running the Complete Test Suite

The repository contains **47 automated tests** covering unit, integration, and all 16 required end-to-end telephone call scenarios:

```bash
python -m pytest -v
```

All 47 tests execute against isolated SQLite in-memory databases and mocked provider adapters, requiring zero external network calls.

---

## 6. Connecting a Real Phone Number

See [docs/GCP_DEPLOYMENT.md](docs/GCP_DEPLOYMENT.md) for full instructions on configuring a Twilio/Telnyx SIP trunk connected to LiveKit Agents for production PSTN telephone calls.
