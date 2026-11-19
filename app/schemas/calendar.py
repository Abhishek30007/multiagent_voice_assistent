from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class CalendarEventOut(BaseModel):
    id: int
    event_id: str
    calendar_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_all_day: bool
    status: str
    organizer_email: Optional[str] = None
    attendees: Optional[str] = None
    html_link: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailabilitySlot(BaseModel):
    start_time: datetime
    end_time: datetime
    is_busy: bool
    conflicting_event_summary: Optional[str] = None


class AvailabilityResponse(BaseModel):
    target_start: datetime
    target_end: datetime
    is_available: bool
    conflicts: List[CalendarEventOut] = []
