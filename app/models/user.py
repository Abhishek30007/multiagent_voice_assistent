from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.token import OAuthToken
    from app.models.email import EmailMessage
    from app.models.calendar import CalendarEvent
    from app.models.sync_state import SyncState


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tokens: Mapped[List["OAuthToken"]] = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    emails: Mapped[List["EmailMessage"]] = relationship("EmailMessage", back_populates="user", cascade="all, delete-orphan")
    calendar_events: Mapped[List["CalendarEvent"]] = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    sync_states: Mapped[List["SyncState"]] = relationship("SyncState", back_populates="user", cascade="all, delete-orphan")
