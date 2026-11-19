import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class CallLog(Base, TimestampMixin):
    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    call_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    caller_number: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    ai_phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    call_start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)
    call_end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    call_status: Mapped[str] = mapped_column(String(32), default="connected", nullable=False)  # connected, completed, interrupted, failed
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    agent_execution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_source_references: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of source IDs
    
    # Cost & latency metrics
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_consumed: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)

    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_user_call_start", "user_id", "call_start_time"),
    )
