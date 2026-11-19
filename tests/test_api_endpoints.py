import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.email import EmailMessage
from app.models.calendar import CalendarEvent


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["components"]["database"] == "connected"


@pytest.mark.asyncio
async def test_email_endpoints(client: AsyncClient, db_session: AsyncSession, test_owner: User):
    # Seed sample emails
    now = datetime.datetime.now(datetime.timezone.utc)
    email1 = EmailMessage(
        user_id=test_owner.id,
        message_id="msg_001",
        thread_id="th_001",
        sender_name="Tech Recruiter",
        sender_email="recruiter@techcorp.com",
        subject="Invitation to Online Assessment - SDE",
        snippet="Please complete your test by tomorrow",
        body_text="Your assessment is tomorrow at 4 PM.",
        received_at=now,
        category="Assessment",
        is_read=False,
    )
    email2 = EmailMessage(
        user_id=test_owner.id,
        message_id="msg_002",
        thread_id="th_002",
        sender_name="HDFC Bank",
        sender_email="alerts@hdfcbank.net",
        subject="Monthly Account Statement",
        snippet="Your statement is ready",
        body_text="Please find your statement attached.",
        received_at=now - datetime.timedelta(days=2),
        category="Finance",
        is_read=True,
    )
    db_session.add_all([email1, email2])
    await db_session.commit()

    # 1. List emails
    res = await client.get("/api/v1/emails")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 2. Filter by category
    res_cat = await client.get("/api/v1/emails?category=Assessment")
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    assert data_cat["total"] == 1
    assert data_cat["items"][0]["message_id"] == "msg_001"

    # 3. Search keyword
    res_search = await client.get("/api/v1/emails?search=statement")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert data_search["total"] == 1
    assert data_search["items"][0]["message_id"] == "msg_002"

    # 4. Email Stats
    res_stats = await client.get("/api/v1/emails/stats/summary")
    assert res_stats.status_code == 200
    stats = res_stats.json()["data"]
    assert stats["total_emails"] == 2
    assert "Assessment" in stats["categories"]
    assert "Finance" in stats["categories"]


@pytest.mark.asyncio
async def test_calendar_availability_endpoints(client: AsyncClient, db_session: AsyncSession, test_owner: User):
    now = datetime.datetime.now(datetime.timezone.utc)
    # Event tomorrow from 16:00 to 17:00 UTC
    tomorrow = (now + datetime.timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow + datetime.timedelta(hours=1)

    event = CalendarEvent(
        user_id=test_owner.id,
        event_id="cal_evt_999",
        summary="Online Assessment Scheduled",
        description="Coding round on platform",
        start_time=tomorrow,
        end_time=tomorrow_end,
        status="confirmed",
    )
    db_session.add(event)
    await db_session.commit()

    # 1. Check availability during conflicting time
    check_start = (tomorrow - datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    check_end = (tomorrow + datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    res_conflict = await client.get(
        f"/api/v1/calendar/availability?start_time={check_start}&end_time={check_end}"
    )
    assert res_conflict.status_code == 200
    conflict_data = res_conflict.json()["data"]
    assert conflict_data["is_available"] is False
    assert len(conflict_data["conflicts"]) == 1
    assert conflict_data["conflicts"][0]["event_id"] == "cal_evt_999"

    # 2. Check availability during free time
    free_start = (tomorrow + datetime.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    free_end = (tomorrow + datetime.timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    res_free = await client.get(
        f"/api/v1/calendar/availability?start_time={free_start}&end_time={free_end}"
    )
    assert res_free.status_code == 200
    free_data = res_free.json()["data"]
    assert free_data["is_available"] is True
    assert len(free_data["conflicts"]) == 0
