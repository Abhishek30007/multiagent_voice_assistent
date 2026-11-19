import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.token import OAuthToken
from app.core.security import encrypt_token, decrypt_token
from app.services.google.oauth import GoogleOAuthManager


@pytest.mark.asyncio
async def test_auth_status_not_connected(client: AsyncClient, test_owner: User):
    response = await client.get("/api/v1/auth/google/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_connected"] is False
    assert data["data"]["owner_email"] == test_owner.email


@pytest.mark.asyncio
async def test_auth_status_connected(client: AsyncClient, db_session: AsyncSession, test_owner: User):
    token = OAuthToken(
        user_id=test_owner.id,
        provider="google",
        encrypted_access_token=encrypt_token("mock-access-token"),
        encrypted_refresh_token=encrypt_token("mock-refresh-token"),
        scopes="https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.readonly",
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
    )
    db_session.add(token)
    await db_session.commit()

    response = await client.get("/api/v1/auth/google/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_connected"] is True
    assert data["data"]["gmail_connected"] is True
    assert data["data"]["calendar_connected"] is True
    assert data["data"]["is_expired"] is False


@pytest.mark.asyncio
async def test_auth_disconnect(client: AsyncClient, db_session: AsyncSession, test_owner: User):
    token = OAuthToken(
        user_id=test_owner.id,
        provider="google",
        encrypted_access_token=encrypt_token("mock-access-token"),
        scopes="https://www.googleapis.com/auth/gmail.readonly",
    )
    db_session.add(token)
    await db_session.commit()

    response = await client.post("/api/v1/auth/google/disconnect")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify token removed from DB
    res = await db_session.execute(select(OAuthToken).where(OAuthToken.user_id == test_owner.id))
    assert res.scalars().first() is None


@pytest.mark.asyncio
async def test_save_or_update_tokens(db_session: AsyncSession, test_owner: User):
    token_payload = {
        "access_token": "secret_access_xyz",
        "refresh_token": "secret_refresh_abc",
        "scopes": "https://www.googleapis.com/auth/gmail.readonly",
        "expiry": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2),
    }

    record = await GoogleOAuthManager.save_or_update_tokens(db_session, test_owner, token_payload)
    assert record.id is not None
    # Verify encrypted in DB
    assert record.encrypted_access_token != "secret_access_xyz"
    assert decrypt_token(record.encrypted_access_token) == "secret_access_xyz"
    assert decrypt_token(record.encrypted_refresh_token) == "secret_refresh_abc"
