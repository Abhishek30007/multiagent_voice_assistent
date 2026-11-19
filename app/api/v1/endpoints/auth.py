import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logger import logger
from app.models.user import User
from app.models.token import OAuthToken
from app.schemas.auth import AuthURLResponse, ConnectionStatusResponse
from app.schemas.common import APIResponse
from app.services.google.oauth import GoogleOAuthManager

router = APIRouter()
settings = get_settings()


async def get_or_create_owner_user(db: AsyncSession) -> User:
    """Helper to retrieve or initialize the primary owner user record."""
    result = await db.execute(select(User).where(User.email == settings.OWNER_EMAIL))
    user = result.scalars().first()
    if not user:
        user = User(
            email=settings.OWNER_EMAIL,
            name=settings.OWNER_NAME,
            is_active=True,
            is_owner=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@router.get("/google/url", response_model=APIResponse[AuthURLResponse], summary="Get Google OAuth Authorization URL")
async def get_google_auth_url(state: str | None = Query(None)):
    """Generate authorization URL for Google OAuth 2.0 flow."""
    try:
        url, gen_state = GoogleOAuthManager.get_authorization_url(state=state)
        return APIResponse(
            success=True,
            message="Authorization URL generated successfully",
            data=AuthURLResponse(authorization_url=url, state=gen_state),
        )
    except Exception as e:
        logger.error(f"Error generating Google Auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}",
        )


@router.get("/google/callback", summary="Google OAuth 2.0 Callback Handler")
async def google_auth_callback(
    code: str = Query(...),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle callback from Google OAuth redirect with authorization code."""
    if error:
        logger.error(f"Google OAuth authorization error: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google authorization failed: {error}")

    try:
        token_data = GoogleOAuthManager.exchange_code_for_tokens(code=code, state=state)
        user = await get_or_create_owner_user(db)
        await GoogleOAuthManager.save_or_update_tokens(db, user, token_data)

        logger.info(f"Successfully saved Google OAuth credentials for user: {user.email}")

        return {
            "success": True,
            "message": "Google account connected successfully! Gmail and Google Calendar access granted.",
            "owner": user.email,
        }
    except Exception as e:
        logger.error(f"Failed to exchange OAuth token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token exchange failed: {str(e)}",
        )


@router.get("/google/status", response_model=APIResponse[ConnectionStatusResponse], summary="Check Google Connection Status")
async def check_google_connection_status(db: AsyncSession = Depends(get_db)):
    """Check if Google OAuth is connected and scopes are authorized."""
    user = await get_or_create_owner_user(db)
    result = await db.execute(
        select(OAuthToken).where(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "google",
        )
    )
    token_record = result.scalars().first()

    if not token_record:
        return APIResponse(
            success=True,
            data=ConnectionStatusResponse(
                is_connected=False,
                owner_name=user.name or settings.OWNER_NAME,
                owner_email=user.email,
                scopes=[],
                expires_at=None,
                is_expired=False,
                gmail_connected=False,
                calendar_connected=False,
            ),
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    is_expired = token_record.expires_at is not None and token_record.expires_at <= now
    scopes_list = token_record.scopes.split(" ") if token_record.scopes else []

    gmail_ok = any("gmail" in s for s in scopes_list)
    calendar_ok = any("calendar" in s for s in scopes_list)

    return APIResponse(
        success=True,
        data=ConnectionStatusResponse(
            is_connected=True,
            owner_name=user.name or settings.OWNER_NAME,
            owner_email=user.email,
            scopes=scopes_list,
            expires_at=token_record.expires_at,
            is_expired=is_expired,
            gmail_connected=gmail_ok,
            calendar_connected=calendar_ok,
        ),
    )


@router.post("/google/disconnect", response_model=APIResponse[dict], summary="Disconnect Google Account")
async def disconnect_google_account(db: AsyncSession = Depends(get_db)):
    """Revoke tokens and delete OAuth credential records."""
    user = await get_or_create_owner_user(db)
    await db.execute(
        delete(OAuthToken).where(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "google",
        )
    )
    await db.commit()

    return APIResponse(
        success=True,
        message="Google account disconnected successfully. Tokens deleted.",
        data={"user_id": user.id, "email": user.email},
    )
