from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, AsyncSessionLocal
from app.core.logger import logger
from app.schemas.sync import SyncStatusResponse, SyncTriggerResponse, ServiceSyncDetail
from app.schemas.common import APIResponse
from app.services.ingestion.sync_manager import SyncManager
from app.services.ingestion.email_ingester import EmailIngestionService
from app.services.ingestion.calendar_ingester import CalendarIngestionService
from app.api.v1.endpoints.auth import get_or_create_owner_user

router = APIRouter()


async def _run_background_sync_all(user_id: int, force_full: bool):
    """Run full sync pipeline in background task."""
    async with AsyncSessionLocal() as session:
        from app.models.user import User
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if user:
            await SyncManager.sync_all_for_user(session, user, force_full=force_full)


async def _run_background_sync_gmail(user_id: int, force_full: bool):
    async with AsyncSessionLocal() as session:
        from app.models.user import User
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if user:
            try:
                await EmailIngestionService.sync_emails(session, user, force_full_sync=force_full)
            except Exception as e:
                logger.error(f"Background email sync failed: {e}")


async def _run_background_sync_calendar(user_id: int, force_full: bool):
    async with AsyncSessionLocal() as session:
        from app.models.user import User
        from sqlalchemy import select
        res = await session.execute(select(User).where(User.id == user_id))
        user = res.scalars().first()
        if user:
            try:
                await CalendarIngestionService.sync_calendar(session, user, force_full_sync=force_full)
            except Exception as e:
                logger.error(f"Background calendar sync failed: {e}")


@router.post("/all", response_model=APIResponse[SyncTriggerResponse], summary="Trigger All Ingestion Sync")
async def trigger_sync_all(
    background_tasks: BackgroundTasks,
    force_full: bool = Query(False, description="Force full window sync instead of incremental sync"),
    db: AsyncSession = Depends(get_db),
):
    """Trigger background synchronization for both Gmail and Calendar."""
    user = await get_or_create_owner_user(db)
    background_tasks.add_task(_run_background_sync_all, user.id, force_full)

    return APIResponse(
        success=True,
        message="Background synchronization started for Gmail and Calendar",
        data=SyncTriggerResponse(
            task_id=f"sync_all_{user.id}",
            status="queued",
            message="Data ingestion pipeline initiated",
        ),
    )


@router.post("/gmail", response_model=APIResponse[SyncTriggerResponse], summary="Trigger Gmail Ingestion Sync")
async def trigger_sync_gmail(
    background_tasks: BackgroundTasks,
    force_full: bool = Query(False, description="Force full window sync instead of incremental sync"),
    db: AsyncSession = Depends(get_db),
):
    """Trigger background synchronization for Gmail emails."""
    user = await get_or_create_owner_user(db)
    background_tasks.add_task(_run_background_sync_gmail, user.id, force_full)

    return APIResponse(
        success=True,
        message="Background synchronization started for Gmail",
        data=SyncTriggerResponse(
            task_id=f"sync_gmail_{user.id}",
            status="queued",
            message="Gmail ingestion initiated",
        ),
    )


@router.post("/calendar", response_model=APIResponse[SyncTriggerResponse], summary="Trigger Calendar Ingestion Sync")
async def trigger_sync_calendar(
    background_tasks: BackgroundTasks,
    force_full: bool = Query(False, description="Force full window sync instead of incremental sync"),
    db: AsyncSession = Depends(get_db),
):
    """Trigger background synchronization for Google Calendar events."""
    user = await get_or_create_owner_user(db)
    background_tasks.add_task(_run_background_sync_calendar, user.id, force_full)

    return APIResponse(
        success=True,
        message="Background synchronization started for Google Calendar",
        data=SyncTriggerResponse(
            task_id=f"sync_calendar_{user.id}",
            status="queued",
            message="Calendar ingestion initiated",
        ),
    )


@router.get("/status", response_model=APIResponse[SyncStatusResponse], summary="Get Data Ingestion Status")
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    """Retrieve the latest synchronization status and stats for all services."""
    user = await get_or_create_owner_user(db)
    status_dict = await SyncManager.get_sync_status(db, user.id)

    services_converted = {
        name: ServiceSyncDetail(**details)
        for name, details in status_dict.get("services", {}).items()
    }

    return APIResponse(
        success=True,
        data=SyncStatusResponse(
            is_syncing=status_dict.get("is_syncing", False),
            services=services_converted,
        ),
    )
