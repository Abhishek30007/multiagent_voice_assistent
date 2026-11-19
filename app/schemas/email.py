from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


class EmailMessageOut(BaseModel):
    id: int
    message_id: str
    thread_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: str
    recipient: Optional[str] = None
    subject: Optional[str] = None
    snippet: Optional[str] = None
    body_text: Optional[str] = None
    received_at: datetime
    category: Optional[str] = None
    is_read: bool = False
    has_attachments: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailStatsOut(BaseModel):
    total_emails: int
    categories: Dict[str, int]
    earliest_email: Optional[datetime] = None
    latest_email: Optional[datetime] = None
