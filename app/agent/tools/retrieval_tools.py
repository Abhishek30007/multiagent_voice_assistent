import datetime
import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, asc

from app.models.email import EmailMessage
from app.models.calendar import CalendarEvent
from app.core.logger import logger


async def search_gmail_records(
    session: AsyncSession,
    user_id: int,
    query_terms: List[str],
    category: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Query stored email messages in PostgreSQL for relevant personal evidence."""
    stmt = select(EmailMessage).where(EmailMessage.user_id == user_id)

    if category:
        stmt = stmt.where(EmailMessage.category.ilike(f"%{category}%"))

    if query_terms:
        term_filters = []
        for term in query_terms:
            clean_term = term.strip().lower()
            if not clean_term:
                continue
            term_filters.append(
                or_(
                    EmailMessage.subject.ilike(f"%{clean_term}%"),
                    EmailMessage.body_text.ilike(f"%{clean_term}%"),
                    EmailMessage.snippet.ilike(f"%{clean_term}%"),
                    EmailMessage.sender_name.ilike(f"%{clean_term}%"),
                    EmailMessage.sender_email.ilike(f"%{clean_term}%"),
                )
            )
        if term_filters:
            stmt = stmt.where(or_(*term_filters))

    stmt = stmt.order_by(desc(EmailMessage.received_at)).limit(limit)
    res = await session.execute(stmt)
    records = res.scalars().all()

    evidence = []
    for r in records:
        evidence.append({
            "source_type": "email",
            "id": r.message_id,
            "subject": r.subject,
            "sender": f"{r.sender_name or ''} <{r.sender_email}>".strip(),
            "date": r.received_at.isoformat(),
            "category": r.category,
            "snippet": r.snippet or "",
            "content": (r.body_text or r.snippet or "")[:600],
        })
    return evidence


async def search_calendar_records(
    session: AsyncSession,
    user_id: int,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    query_terms: Optional[List[str]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Query stored calendar events in PostgreSQL for schedule evidence."""
    stmt = select(CalendarEvent).where(
        and_(
            CalendarEvent.user_id == user_id,
            CalendarEvent.status != "cancelled",
        )
    )

    if start_time and end_time:
        # Overlapping condition: event starts before end_time and ends after start_time
        stmt = stmt.where(
            and_(
                CalendarEvent.start_time < end_time,
                CalendarEvent.end_time > start_time,
            )
        )
    elif start_time:
        stmt = stmt.where(CalendarEvent.end_time >= start_time)

    if query_terms:
        term_filters = []
        for term in query_terms:
            clean = term.strip().lower()
            if not clean:
                continue
            term_filters.append(
                or_(
                    CalendarEvent.summary.ilike(f"%{clean}%"),
                    CalendarEvent.description.ilike(f"%{clean}%"),
                    CalendarEvent.location.ilike(f"%{clean}%"),
                )
            )
        if term_filters:
            stmt = stmt.where(or_(*term_filters))

    stmt = stmt.order_by(asc(CalendarEvent.start_time)).limit(limit)
    res = await session.execute(stmt)
    records = res.scalars().all()

    evidence = []
    for r in records:
        evidence.append({
            "source_type": "calendar",
            "id": r.event_id,
            "summary": r.summary,
            "description": r.description or "",
            "location": r.location or "",
            "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat(),
            "is_all_day": r.is_all_day,
            "status": r.status,
            "organizer": r.organizer_email,
        })
    return evidence
