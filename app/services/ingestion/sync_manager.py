from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logger import logger
from app.core.redis_client import DistributedSyncLock
from app.models.user import User
from app.models.sync_state import SyncState
from app.services.ingestion.email_ingester import EmailIngestionService
from app.services.ingestion.calendar_ingester import CalendarIngestionService


class SyncManager:
    """Orchestrates multi-service data ingestion with Redis distributed concurrency locking."""

    @classmethod
    async def sync_all_for_user(cls, session: AsyncSession, user: User, force_full: bool = False) -> Dict[str, Any]:
        """Trigger sync for both Gmail and Google Calendar under a distributed lock."""
        lock_name = f"sync:user:{user.id}"
        async with DistributedSyncLock(lock_name, timeout_seconds=600) as acquired:
            if not acquired:
                logger.warning(f"Sync already running for user {user.id}. Skipping concurrent run.")
                return {
                    "success": False,
                    "message": "A synchronization process is already in progress for this account.",
                }

            results = {}
            # 1. Sync Gmail
            try:
                emails_synced, email_msg = await EmailIngestionService.sync_emails(
                    session=session, user=user, force_full_sync=force_full
                )
                results["gmail"] = {"success": True, "items_synced": emails_synced, "message": email_msg}
            except Exception as e:
                logger.error(f"Gmail sync failed: {e}")
                results["gmail"] = {"success": False, "error": str(e)}

            # 2. Sync Google Calendar
            try:
                events_synced, cal_msg = await CalendarIngestionService.sync_calendar(
                    session=session, user=user, force_full_sync=force_full
                )
                results["calendar"] = {"success": True, "items_synced": events_synced, "message": cal_msg}
            except Exception as e:
                logger.error(f"Calendar sync failed: {e}")
                results["calendar"] = {"success": False, "error": str(e)}

            return {
                "success": True,
                "services": results,
            }

    @classmethod
    async def get_sync_status(cls, session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """Retrieve the latest sync health and timestamps for all services."""
        result = await session.execute(
            select(SyncState).where(SyncState.user_id == user_id)
        )
        states = result.scalars().all()
        services_dict = {}
        is_any_syncing = False

        for st in states:
            if st.sync_status == "running":
                is_any_syncing = True
            services_dict[st.service_name] = {
                "service_name": st.service_name,
                "sync_status": st.sync_status,
                "items_synced": st.items_synced,
                "last_sync_started_at": st.last_sync_started_at,
                "last_sync_completed_at": st.last_sync_completed_at,
                "error_message": st.error_message,
            }

        return {
            "is_syncing": is_any_syncing,
            "services": services_dict,
        }
