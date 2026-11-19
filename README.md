# Personal AI Twin – Phase 1: Real-Time Data Ingestion Engine

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3%2B-37814A.svg)](https://docs.celeryq.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Phase 1 implementation of Abhishek's **Personal AI Twin**. This phase establishes the core foundational infrastructure: **Google OAuth 2.0 authorization, Gmail & Google Calendar data ingestion, PostgreSQL relational storage, Redis distributed locking/caching, Celery background sync workers, and FastAPI REST endpoints**.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Google Cloud APIs       │
                          │   - Gmail API (v1)        │
                          │   - Google Calendar (v3)  │
                          └─────────────┬─────────────┘
                                        │ OAuth 2.0 Tokens
                                        ▼ (Fernet Encrypted)
┌───────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND                             │
│                                                                           │
│   ┌────────────────────┐   ┌─────────────────────┐   ┌────────────────┐   │
│   │   Auth & Security  │   │  Ingestion Pipeline │   │  API Endpoints │   │
│   │   - OAuth Flow     │   │  - Email Ingestion  │   │  - /auth       │   │
│   │   - Token Crypto   │   │  - Calendar Ingest  │   │  - /emails     │   │
│   │   - Fernet 256-bit │   │  - Auto-Categorizer │   │  - /calendar   │   │
│   └────────────────────┘   └──────────┬──────────┘   │  - /sync       │   │
│                                       │              │  - /health     │   │
│                                       │              └────────────────┘   │
└───────────────────────────────────────┼───────────────────────────────────┘
                                        │
           ┌────────────────────────────┴───────────────────────────┐
           ▼                                                        ▼
┌───────────────────────────┐                            ┌──────────────────────────┐
│   PostgreSQL 16           │                            │   Redis 7                │
│   - users                 │                            │   - Distributed Sync Lock│
│   - oauth_tokens (crypt)  │                            │   - Celery Message Broker│
│   - email_messages        │                            │   - Fast Cache           │
│   - calendar_events       │                            └──────────┬───────────────┘
│   - sync_states           │                                       │
└───────────────────────────┘                                       ▼
                                                         ┌──────────────────────────┐
                                                         │   Celery Background      │
                                                         │   - Worker (Data Sync)   │
                                                         │   - Beat (15m Scheduler) │
                                                         └──────────────────────────┘
```

---

## Features Implemented in Phase 1

1. **Google OAuth 2.0 Integration**:
   - Secure authorization URL generation (`offline` access type for refresh tokens).
   - Exchange authorization codes for access and refresh tokens.
   - Automatic token refresh upon expiration.
   - Token revocation on disconnect.

2. **Security & Privacy by Design**:
   - Only **read-only** Google scopes requested (`gmail.readonly`, `calendar.readonly`).
   - Symmetrically encrypted token storage at rest using **Fernet (AES-128-CBC with SHA256 HMAC)**.
   - Plain credentials never logged or exposed in API responses.

3. **Gmail Ingestion Engine**:
   - Full message retrieval with recursive MIME multipart traversal.
   - Text extraction, HTML stripping, sender, recipient, and date parsing into UTC.
   - Built-in categorization (`Assessment`, `Interview`, `Career`, `Finance`, `Security`, `Meeting`, `General`).
   - Incremental synchronization powered by Gmail `historyId`.
   - Idempotent upserts ensuring no duplicate emails in the database.

4. **Google Calendar Ingestion Engine**:
   - Ingestion of primary calendar events with recurrence expansion.
   - Conversion of all event times to standardized UTC.
   - Detection and parsing of all-day vs timed events, attendees, and meeting links.
   - Incremental synchronization using Google Calendar `syncToken` with automatic 410-Gone fallback.
   - Real-time availability conflict checker (`/api/v1/calendar/availability`).

5. **PostgreSQL & Alembic**:
   - Strict relational schema for `users`, `oauth_tokens`, `email_messages`, `calendar_events`, and `sync_states`.
   - Indexed queries for rapid search by sender, received date, event start/end, and category.
   - Production-ready Alembic migration versions.

6. **Redis Distributed Locking & Celery**:
   - Redis distributed lock (`DistributedSyncLock`) preventing duplicate concurrent sync runs.
   - In-memory lock fallback when Redis is offline.
   - Celery background workers and Celery Beat scheduler for automated incremental sync every 15 minutes.

7. **FastAPI REST API**:
   - Full interactive Swagger documentation at `/docs` and ReDoc at `/redoc`.
   - Health readiness checks at `/api/v1/health`.

---

## Directory Structure

```
multiagent_voice_assistent/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── Dockerfile                # Multi-stage container definition
├── docker-compose.yml        # Orchestration (DB, Redis, Backend, Celery)
├── requirements.txt          # Python dependencies
├── alembic.ini               # Alembic configuration
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_phase1_schema.py
├── app/
│   ├── __init__.py
│   ├── main.py               # Application entrypoint & lifespan
│   ├── core/
│   │   ├── config.py         # Pydantic BaseSettings
│   │   ├── database.py       # Async & Sync SQLAlchemy sessions
│   │   ├── logger.py         # Structured logging configuration
│   │   ├── redis_client.py   # Redis connection & distributed lock
│   │   └── security.py       # Fernet encryption for OAuth tokens
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── email.py
│   │   ├── calendar.py
│   │   └── sync_state.py
│   ├── schemas/
│   │   ├── common.py
│   │   ├── auth.py
│   │   ├── email.py
│   │   ├── calendar.py
│   │   └── sync.py
│   ├── services/
│   │   ├── google/
│   │   │   ├── oauth.py
│   │   │   ├── gmail_service.py
│   │   │   └── calendar_service.py
│   │   └── ingestion/
│   │       ├── email_ingester.py
│   │       ├── calendar_ingester.py
│   │       └── sync_manager.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── emails.py
│   │           ├── calendar.py
│   │           ├── sync.py
│   │           └── health.py
│   └── workers/
│       ├── celery_app.py
│       └── tasks.py
└── tests/
    ├── conftest.py
    ├── test_crypto.py
    ├── test_email_ingestion.py
    ├── test_calendar_ingestion.py
    ├── test_auth.py
    ├── test_api_endpoints.py
    └── test_sync_manager.py
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- (Optional for containerized run) Docker and Docker Compose

### 2. Configure Google Cloud Console
1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `Personal-AI-Twin`.
3. Enable **Gmail API** and **Google Calendar API**.
4. In **OAuth consent screen**:
   - User Type: **External**
   - Scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/calendar.readonly`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Add your Gmail (`abhishekkumarsaw414@gmail.com`) as a Test User.
5. In **Credentials**:
   - Create **OAuth 2.0 Client ID** -> **Web application**.
   - Authorized redirect URIs: `http://localhost:8000/api/v1/auth/google/callback`.
   - Copy Client ID and Client Secret.

### 3. Local Setup

Copy the environment file:
```bash
cp .env.example .env
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run Alembic migrations:
```bash
alembic upgrade head
```

Run the FastAPI application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 4. Running with Docker Compose

To start PostgreSQL, Redis, FastAPI, Celery Worker, and Celery Beat in one command:
```bash
docker-compose up --build
```

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health and readiness check |
| `GET` | `/api/v1/auth/google/url` | Generate Google OAuth consent URL |
| `GET` | `/api/v1/auth/google/callback` | OAuth callback handler |
| `GET` | `/api/v1/auth/google/status` | Connection status for Gmail & Calendar |
| `POST` | `/api/v1/auth/google/disconnect` | Revoke and delete credentials |
| `GET` | `/api/v1/emails` | Paginated emails with filtering & search |
| `GET` | `/api/v1/emails/{id}` | Detailed email view |
| `GET` | `/api/v1/emails/stats/summary` | Email count breakdown by category |
| `GET` | `/api/v1/calendar/events` | List events within date window |
| `GET` | `/api/v1/calendar/events/{id}` | Detailed calendar event view |
| `GET` | `/api/v1/calendar/availability` | Free/busy conflict detection |
| `POST` | `/api/v1/sync/all` | Trigger full ingestion sync |
| `POST` | `/api/v1/sync/gmail` | Trigger Gmail ingestion sync |
| `POST` | `/api/v1/sync/calendar` | Trigger Calendar ingestion sync |
| `GET` | `/api/v1/sync/status` | Ingestion status and item counts |

---

## Running the Test Suite

The test suite runs with in-memory SQLite and mocks, requiring no running database or external network access:

```bash
pytest -v
```
