import datetime
from typing import Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.logger import logger
from app.core.config import get_settings
from app.models.user import User
from app.models.email import EmailMessage
from app.models.sync_state import SyncState
from app.services.google.oauth import GoogleOAuthManager
from app.services.google.gmail_service import GmailClient

settings = get_settings()


class EmailIngestionService:
    """Service responsible for syncing emails from Gmail into PostgreSQL."""

    @classmethod
    async def sync_emails(
        cls,
        session: AsyncSession,
        user: User,
        max_days: int = 30,
        force_full_sync: bool = False,
    ) -> Tuple[int, str]:
        """Sync emails for the user. Returns (count_of_ingested_emails, status_message)."""
        credentials = await GoogleOAuthManager.get_credentials(session, user.id)
        if not credentials:
            raise ValueError(f"No active Google OAuth credentials found for user {user.email}")

        gmail_client = GmailClient(credentials)

        # Retrieve or create SyncState record
        result = await session.execute(
            select(SyncState).where(
                and_(SyncState.user_id == user.id, SyncState.service_name == "gmail")
            )
        )
        sync_state = result.scalars().first()
        if not sync_state:
            sync_state = SyncState(user_id=user.id, service_name="gmail", sync_status="running")
            session.add(sync_state)
            await session.commit()
            await session.refresh(sync_state)

        sync_state.sync_status = "running"
        sync_state.last_sync_started_at = datetime.datetime.now(datetime.timezone.utc)
        sync_state.error_message = None
        await session.commit()

        total_synced = 0
        latest_history_id: Optional[str] = None

        try:
            # Check if incremental sync is feasible
            performed_incremental = False
            msg_ids_to_fetch: List[str] = []

            if sync_state.history_id and not force_full_sync:
                try:
                    logger.info(f"Attempting incremental Gmail sync using historyId {sync_state.history_id}")
                    msg_ids, new_hist_id = gmail_client.get_history(sync_state.history_id)
                    msg_ids_to_fetch = msg_ids
                    latest_history_id = new_hist_id
                    performed_incremental = True
                    logger.info(f"Incremental sync discovered {len(msg_ids_to_fetch)} new/updated messages")
                except Exception as ex:
                    logger.warning(f"Incremental sync failed ({ex}); falling back to windowed sync")

            if not performed_incremental:
                # Windowed sync
                cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=max_days)).strftime("%Y/%m/%d")
                query = f"after:{cutoff_date}"
                logger.info(f"Executing Gmail windowed query: '{query}'")

                page_token = None
                fetched_ids = []
                while True:
                    ids, page_token = gmail_client.list_message_ids(
                        query=query,
                        max_results=settings.GMAIL_MAX_RESULTS_PER_PAGE,
                        page_token=page_token,
                    )
                    fetched_ids.extend(ids)
                    if not page_token or len(fetched_ids) >= 500:
                        break

                msg_ids_to_fetch = fetched_ids
                # Get current profile history ID
                try:
                    profile = gmail_client.get_profile()
                    latest_history_id = str(profile.get("historyId"))
                except Exception:
                    latest_history_id = None

            # Process and store messages
            for msg_id in msg_ids_to_fetch:
                try:
                    # Check if message already exists in DB
                    existing = await session.execute(
                        select(EmailMessage).where(
                            and_(
                                EmailMessage.user_id == user.id,
                                EmailMessage.message_id == msg_id,
                            )
                        )
                    )
                    email_record = existing.scalars().first()

                    raw_msg = gmail_client.get_message(msg_id)
                    parsed = GmailClient.parse_email_payload(raw_msg)

                    if email_record:
                        # Update flags/labels
                        email_record.labels = parsed["labels"]
                        email_record.is_read = parsed["is_read"]
                    else:
                        email_record = EmailMessage(
                            user_id=user.id,
                            **parsed,
                        )
                        session.add(email_record)
                        total_synced += 1

                except Exception as msg_err:
                    logger.error(f"Error ingesting email {msg_id}: {msg_err}")
                    continue

            # Update sync state to success
            sync_state.sync_status = "success"
            sync_state.last_sync_completed_at = datetime.datetime.now(datetime.timezone.utc)
            sync_state.items_synced = total_synced
            if latest_history_id:
                sync_state.history_id = latest_history_id

            await session.commit()
            return total_synced, f"Successfully ingested {total_synced} emails"

        except Exception as e:
            sync_state.sync_status = "failed"
            sync_state.error_message = str(e)
            await session.commit()
            logger.error(f"Gmail sync failed: {e}")
            raise
