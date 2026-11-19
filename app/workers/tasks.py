import asyncio
from app.workers.celery_app import celery_app
from app.core.logger import logger
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.services.ingestion.sync_manager import SyncManager
from sqlalchemy import select


@celery_app.task(name="app.workers.tasks.task_sync_user_data", bind=True, max_retries=3)
def task_sync_user_data(self, user_id: int, force_full: bool = False):
    """Background task to sync Gmail and Calendar data for a specific user."""
    logger.info(f"Starting background sync task for user_id={user_id} (force_full={force_full})")

    async def _run():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if not user:
                logger.error(f"User with ID {user_id} not found for sync task")
                return {"success": False, "error": "User not found"}
            
            res = await SyncManager.sync_all_for_user(session, user, force_full=force_full)
            return res

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run())
        loop.close()
        return result
    except Exception as exc:
        logger.error(f"Background sync task failed for user_id={user_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.workers.tasks.task_scheduled_sync_all")
def task_scheduled_sync_all():
    """Periodic Celery Beat task that triggers incremental sync for all active users."""
    logger.info("Executing scheduled periodic incremental sync for all users")

    async def _dispatch_all():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()
            for u in users:
                task_sync_user_data.delay(user_id=u.id, force_full=False)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_dispatch_all())
    loop.close()
