from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.auth import AuthURLResponse, OAuthCallbackQuery, ConnectionStatusResponse
from app.schemas.email import EmailMessageOut, EmailStatsOut
from app.schemas.calendar import CalendarEventOut, AvailabilityResponse
from app.schemas.sync import SyncStatusResponse, SyncTriggerResponse, ServiceSyncDetail

__all__ = [
    "APIResponse",
    "PaginatedResponse",
    "AuthURLResponse",
    "OAuthCallbackQuery",
    "ConnectionStatusResponse",
    "EmailMessageOut",
    "EmailStatsOut",
    "CalendarEventOut",
    "AvailabilityResponse",
    "SyncStatusResponse",
    "SyncTriggerResponse",
    "ServiceSyncDetail",
]
