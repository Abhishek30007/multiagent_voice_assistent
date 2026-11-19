from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.sync_state import SyncState
from app.services.ingestion.sync_manager import SyncManager


@pytest.mark.asyncio
async def test_get_sync_status(db_session: AsyncSession, test_owner: User):
    state1 = SyncState(
        user_id=test_owner.id,
        service_name="gmail",
        sync_status="success",
        items_synced=42,
    )
    state2 = SyncState(
        user_id=test_owner.id,
        service_name="calendar",
        sync_status="idle",
        items_synced=15,
    )
    db_session.add_all([state1, state2])
    await db_session.commit()

    status = await SyncManager.get_sync_status(db_session, test_owner.id)
    assert status["is_syncing"] is False
    assert status["services"]["gmail"]["items_synced"] == 42
    assert status["services"]["calendar"]["items_synced"] == 15


@pytest.mark.asyncio
async def test_sync_trigger_api(client: AsyncClient, test_owner: User):
    with patch("app.api.v1.endpoints.sync._run_background_sync_all") as mock_sync:
        res = await client.post("/api/v1/sync/all")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["status"] == "queued"
