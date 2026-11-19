from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logger import setup_logging, logger
from app.core.database import init_db
from app.core.redis_client import close_redis_client
from app.api.v1.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: sets up DB tables and teardowns connections."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    await close_redis_client()
    logger.info("Cleanup completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Personal AI Twin Phase 1: Real-time Data Ingestion Engine for Gmail and Google Calendar with PostgreSQL, Redis, and FastAPI.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (allowing frontend dashboard or external callers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "phase": "Phase 1 - Data Ingestion, PostgreSQL, Redis, FastAPI, Gmail & Calendar Integration",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
