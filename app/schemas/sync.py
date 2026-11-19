from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel


class ServiceSyncDetail(BaseModel):
    service_name: str
    sync_status: str
    items_synced: int
    last_sync_started_at: Optional[datetime] = None
    last_sync_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SyncStatusResponse(BaseModel):
    is_syncing: bool
    services: Dict[str, ServiceSyncDetail]


class SyncTriggerResponse(BaseModel):
    task_id: Optional[str] = None
    status: str
    message: str
