import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class SyncState(Base, TimestampMixin):
    __tablename__ = "sync_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    service_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "gmail" or "calendar"
    
    # State tokens for incremental updates
    sync_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    history_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    
    # Sync timestamps and health
    last_sync_started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="idle", nullable=False)  # "idle", "running", "success", "failed"
    items_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sync_states")

    __table_args__ = (
        Index("idx_user_service", "user_id", "service_name", unique=True),
    )
