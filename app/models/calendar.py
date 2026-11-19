import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class CalendarEvent(Base, TimestampMixin):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Google Calendar event identifier
    event_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary", nullable=False)
    
    # Event details
    summary: Mapped[str | None] = mapped_column(String(512), index=True, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    # Event timings in UTC
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Status and participants
    status: Mapped[str] = mapped_column(String(64), default="confirmed", nullable=False)  # confirmed, tentative, cancelled
    organizer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attendees: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON formatted list of attendees
    recurrence: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_link: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="calendar_events")

    __table_args__ = (
        Index("idx_user_event_id", "user_id", "event_id", unique=True),
        Index("idx_user_event_time", "user_id", "start_time", "end_time"),
    )
