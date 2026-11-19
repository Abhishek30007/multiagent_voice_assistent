import json
import datetime
import pytest
from app.services.google.calendar_service import CalendarClient


def test_parse_timed_calendar_event():
    raw_event = {
        "id": "evt_abc123456",
        "summary": "Online Assessment: Google Round 1",
        "description": "Please join with webcam on: https://meet.google.com/xyz-abc",
        "location": "Google Meet",
        "status": "confirmed",
        "htmlLink": "https://calendar.google.com/event?eid=abc",
        "start": {
            "dateTime": "2026-11-20T16:00:00+05:30",
        },
        "end": {
            "dateTime": "2026-11-20T17:30:00+05:30",
        },
        "organizer": {
            "email": "interviewer@google.com",
            "displayName": "Google Staff",
        },
        "attendees": [
            {"email": "abhishekkumarsaw414@gmail.com", "responseStatus": "accepted"},
            {"email": "interviewer@google.com", "responseStatus": "accepted"},
        ],
    }

    parsed = CalendarClient.parse_calendar_event(raw_event, calendar_id="primary")

    assert parsed["event_id"] == "evt_abc123456"
    assert parsed["summary"] == "Online Assessment: Google Round 1"
    assert parsed["is_all_day"] is False
    assert parsed["organizer_email"] == "interviewer@google.com"
    assert parsed["status"] == "confirmed"
    
    # Check UTC conversion: 16:00:00+05:30 = 10:30:00 UTC
    assert parsed["start_time"].tzinfo == datetime.timezone.utc
    assert parsed["start_time"].hour == 10
    assert parsed["start_time"].minute == 30

    # Attendees serialized JSON check
    attendees = json.loads(parsed["attendees"])
    assert len(attendees) == 2
    assert attendees[0]["email"] == "abhishekkumarsaw414@gmail.com"


def test_parse_all_day_calendar_event():
    raw_event = {
        "id": "all_day_123",
        "summary": "National Holiday",
        "status": "confirmed",
        "start": {
            "date": "2026-12-25",
        },
        "end": {
            "date": "2026-12-25",
        },
    }

    parsed = CalendarClient.parse_calendar_event(raw_event, calendar_id="primary")

    assert parsed["event_id"] == "all_day_123"
    assert parsed["is_all_day"] is True
    assert parsed["start_time"].day == 25
    assert parsed["start_time"].month == 12
