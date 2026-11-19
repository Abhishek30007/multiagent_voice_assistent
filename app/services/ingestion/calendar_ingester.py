import datetime
from typing import Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from googleapiclient.errors import HttpError

from app.core.logger import logger
from app.core.config import get_settings
from app.models.user import User
from app.models.calendar import CalendarEvent
from app.models.sync_state import SyncState
from app.services.google.oauth import GoogleOAuthManager
from app.services.google.calendar_service import CalendarClient

settings = get_settings()


class CalendarIngestionService:
    """Service responsible for syncing events from Google Calendar into PostgreSQL."""

    @classmethod
    async def sync_calendar(
        cls,
        session: AsyncSession,
        user: User,
        days_past: int = 30,
        days_future: int = 90,
        force_full_sync: bool = False,
    ) -> Tuple[int, str]:
        """Sync calendar events for the user. Returns (count_of_ingested_events, status_message)."""
        credentials = await GoogleOAuthManager.get_credentials(session, user.id)
        if not credentials:
            raise ValueError(f"No active Google OAuth credentials found for user {user.email}")

        calendar_client = CalendarClient(credentials)

        # Retrieve or create SyncState record
        result = await session.execute(
            select(SyncState).where(
                and_(SyncState.user_id == user.id, SyncState.service_name == "calendar")
            )
        )
        sync_state = result.scalars().first()
        if not sync_state:
            sync_state = SyncState(user_id=user.id, service_name="calendar", sync_status="running")
            session.add(sync_state)
            await session.commit()
            await session.refresh(sync_state)

        sync_state.sync_status = "running"
        sync_state.last_sync_started_at = datetime.datetime.now(datetime.timezone.utc)
        sync_state.error_message = None
        await session.commit()

        total_synced = 0
        new_sync_token: Optional[str] = None

        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            time_min = now - datetime.timedelta(days=days_past)
            time_max = now + datetime.timedelta(days=days_future)

            sync_token_to_use = sync_state.sync_token if not force_full_sync else None
            page_token = None
            raw_events: List[dict] = []

            try:
                while True:
                    events, page_token, next_sync = calendar_client.list_events(
                        calendar_id="primary",
                        time_min=time_min if not sync_token_to_use else None,
                        time_max=time_max if not sync_token_to_use else None,
                        sync_token=sync_token_to_use,
                        page_token=page_token,
                    )
                    raw_events.extend(events)
                    if next_sync:
                        new_sync_token = next_sync
                    if not page_token:
                        break

            except HttpError as http_err:
                if http_err.resp.status == 410:
                    # Sync token expired / invalidated by Google, fallback to full sync
                    logger.warning("Calendar sync token expired (410 Gone). Performing full window sync.")
                    sync_token_to_use = None
                    page_token = None
                    raw_events = []
                    while True:
                        events, page_token, next_sync = calendar_client.list_events(
                            calendar_id="primary",
                            time_min=time_min,
                            time_max=time_max,
                            sync_token=None,
                            page_token=page_token,
                        )
                        raw_events.extend(events)
                        if next_sync:
                            new_sync_token = next_sync
                        if not page_token:
                            break
                else:
                    raise

            # Upsert events into database
            for raw_evt in raw_events:
                parsed = CalendarClient.parse_calendar_event(raw_evt, calendar_id="primary")
                event_id = parsed["event_id"]
                if not event_id:
                    continue

                existing = await session.execute(
                    select(CalendarEvent).where(
                        and_(
                            CalendarEvent.user_id == user.id,
                            CalendarEvent.event_id == event_id,
                        )
                    )
                )
                event_record = existing.scalars().first()

                if event_record:
                    # Update fields
                    for key, val in parsed.items():
                        setattr(event_record, key, val)
                else:
                    event_record = CalendarEvent(
                        user_id=user.id,
                        **parsed,
                    )
                    session.add(event_record)
                    total_synced += 1

            # Update sync state to success
            sync_state.sync_status = "success"
            sync_state.last_sync_completed_at = datetime.datetime.now(datetime.timezone.utc)
            sync_state.items_synced = len(raw_events)
            if new_sync_token:
                sync_state.sync_token = new_sync_token

            await session.commit()
            return total_synced, f"Successfully processed {len(raw_events)} calendar events ({total_synced} new)"

        except Exception as e:
            sync_state.sync_status = "failed"
            sync_state.error_message = str(e)
            await session.commit()
            logger.error(f"Calendar sync failed: {e}")
            raise
