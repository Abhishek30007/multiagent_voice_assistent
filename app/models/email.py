import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class EmailMessage(Base, TimestampMixin):
    __tablename__ = "email_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Gmail specific identifiers
    message_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    
    # Headers and metadata
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    recipient: Mapped[str | None] = mapped_column(Text, nullable=True)
    cc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bcc: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, index=True, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Message content
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps and flags
    received_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    labels: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or comma-separated list
    category: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="emails")

    __table_args__ = (
        Index("idx_user_msg_id", "user_id", "message_id", unique=True),
        Index("idx_user_received_at", "user_id", "received_at"),
    )
