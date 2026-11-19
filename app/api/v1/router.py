from fastapi import APIRouter
from app.api.v1.endpoints import auth, emails, calendar, sync, health, agent, voice, calls

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Google OAuth"])
api_router.include_router(emails.router, prefix="/emails", tags=["Emails"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["Calendar"])
api_router.include_router(sync.router, prefix="/sync", tags=["Data Ingestion & Sync"])
api_router.include_router(agent.router, prefix="/agent", tags=["Multi-Agent Reasoning"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice Engine"])
api_router.include_router(calls.router, prefix="/calls", tags=["Call Management"])
