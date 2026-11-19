import datetime
from typing import Tuple, Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import encrypt_token, decrypt_token
from app.core.logger import logger
from app.models.user import User
from app.models.token import OAuthToken

settings = get_settings()


class GoogleOAuthManager:
    @staticmethod
    def get_flow(state: Optional[str] = None) -> Flow:
        """Create and configure a Google OAuth2 Flow instance."""
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=settings.GOOGLE_SCOPES,
            state=state,
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    @classmethod
    def get_authorization_url(cls, state: Optional[str] = None) -> Tuple[str, str]:
        """Generate Google OAuth 2.0 authorization URL."""
        flow = cls.get_flow(state=state)
        # access_type='offline' is required to obtain a refresh token
        authorization_url, generated_state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, generated_state

    @classmethod
    def exchange_code_for_tokens(cls, code: str, state: Optional[str] = None) -> dict:
        """Exchange the received authorization code for access and refresh tokens."""
        flow = cls.get_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "scopes": " ".join(credentials.scopes) if credentials.scopes else "",
            "expiry": credentials.expiry,
        }

    @classmethod
    async def save_or_update_tokens(
        cls,
        session: AsyncSession,
        user: User,
        token_data: dict,
    ) -> OAuthToken:
        """Encrypt and persist OAuth tokens in PostgreSQL."""
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user.id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalars().first()

        encrypted_access = encrypt_token(token_data["access_token"])
        encrypted_refresh = encrypt_token(token_data.get("refresh_token"))

        expiry = token_data.get("expiry")
        if expiry and isinstance(expiry, datetime.datetime) and expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=datetime.timezone.utc)

        if token_record:
            token_record.encrypted_access_token = encrypted_access
            if encrypted_refresh:  # Keep existing refresh token if Google didn't return a new one
                token_record.encrypted_refresh_token = encrypted_refresh
            token_record.scopes = token_data.get("scopes", "")
            token_record.expires_at = expiry
            token_record.token_uri = token_data.get("token_uri", "https://oauth2.googleapis.com/token")
        else:
            token_record = OAuthToken(
                user_id=user.id,
                provider="google",
                encrypted_access_token=encrypted_access,
                encrypted_refresh_token=encrypted_refresh,
                scopes=token_data.get("scopes", ""),
                expires_at=expiry,
                token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            )
            session.add(token_record)

        await session.commit()
        await session.refresh(token_record)
        return token_record

    @classmethod
    async def get_credentials(
        cls,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[Credentials]:
        """Retrieve stored tokens, decrypt them, refresh if expired, and return Google Credentials."""
        result = await session.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == "google",
            )
        )
        token_record = result.scalars().first()
        if not token_record:
            return None

        access_token = decrypt_token(token_record.encrypted_access_token)
        refresh_token = decrypt_token(token_record.encrypted_refresh_token)

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_record.token_uri,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=token_record.scopes.split(" ") if token_record.scopes else settings.GOOGLE_SCOPES,
        )

        # Check if token is expired and refresh if necessary
        if credentials.expired or (token_record.expires_at and token_record.expires_at <= datetime.datetime.now(datetime.timezone.utc)):
            if refresh_token:
                try:
                    logger.info(f"Refreshing expired Google OAuth access token for user {user_id}")
                    credentials.refresh(Request())
                    # Update DB with new access token
                    token_record.encrypted_access_token = encrypt_token(credentials.token)
                    if credentials.expiry:
                        exp = credentials.expiry
                        if exp.tzinfo is None:
                            exp = exp.replace(tzinfo=datetime.timezone.utc)
                        token_record.expires_at = exp
                    await session.commit()
                except Exception as e:
                    logger.error(f"Failed to refresh Google OAuth token: {e}")
                    raise

        return credentials
