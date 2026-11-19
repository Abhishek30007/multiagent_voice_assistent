import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis_client import get_redis_client
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("", summary="System Health and Readiness Check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check database, redis, and application status."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        redis_ok = False

    status = "healthy" if db_ok else "degraded"

    return {
        "status": status,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "components": {
            "database": "connected" if db_ok else "unreachable",
            "redis": "connected" if redis_ok else "unreachable (fallback active)",
        },
    }
