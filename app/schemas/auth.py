from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class AuthURLResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthCallbackQuery(BaseModel):
    code: str
    state: Optional[str] = None
    error: Optional[str] = None


class ConnectionStatusResponse(BaseModel):
    is_connected: bool
    owner_name: str
    owner_email: str
    provider: str = "google"
    scopes: List[str] = []
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    gmail_connected: bool = False
    calendar_connected: bool = False
