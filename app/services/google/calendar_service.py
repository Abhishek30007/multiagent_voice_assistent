import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import dateutil.parser
from app.core.logger import logger


class CalendarClient:
    """Client for querying the Google Calendar REST API."""

    def __init__(self, credentials: Credentials):
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[datetime.datetime] = None,
        time_max: Optional[datetime.datetime] = None,
        sync_token: Optional[str] = None,
        page_token: Optional[str] = None,
        max_results: int = 250,
    ) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
        """Fetch events from Google Calendar.
        
        Returns:
            Tuple of (events_list, next_page_token, next_sync_token)
        """
        params: Dict[str, Any] = {
            "calendarId": calendar_id,
            "maxResults": min(max_results, 250),
            "singleEvents": True,  # Expand recurring events into individual instances
            "orderBy": "startTime",
        }

        if sync_token:
            # When syncToken is specified, timeMin/timeMax must NOT be provided
            params["syncToken"] = sync_token
            # singleEvents cannot be used with syncToken in some calendar API configs,
            # but if expanding is needed, we handle it
            params.pop("orderBy", None)
        else:
            if time_min:
                params["timeMin"] = time_min.isoformat()
            if time_max:
                params["timeMax"] = time_max.isoformat()

        if page_token:
            params["pageToken"] = page_token

        response = self.service.events().list(**params).execute()
        events = response.get("items", [])
        next_page_token = response.get("nextPageToken")
        next_sync_token = response.get("nextSyncToken")

        return events, next_page_token, next_sync_token

    @classmethod
    def parse_calendar_event(cls, raw: Dict[str, Any], calendar_id: str = "primary") -> Dict[str, Any]:
        """Convert a raw Google Calendar API event dict into a structured model dict."""
        event_id = raw.get("id", "")
        summary = raw.get("summary", "(No Title)")
        description = raw.get("description")
        location = raw.get("location")
        status = raw.get("status", "confirmed")
        html_link = raw.get("htmlLink")

        # Parse start and end times
        start_dict = raw.get("start", {})
        end_dict = raw.get("end", {})

        is_all_day = False
        start_time: datetime.datetime
        end_time: datetime.datetime

        if "dateTime" in start_dict:
            start_time = dateutil.parser.parse(start_dict["dateTime"]).astimezone(datetime.timezone.utc)
        elif "date" in start_dict:
            # Full day event (format YYYY-MM-DD)
            is_all_day = True
            d = datetime.date.fromisoformat(start_dict["date"])
            start_time = datetime.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        else:
            start_time = datetime.datetime.now(datetime.timezone.utc)

        if "dateTime" in end_dict:
            end_time = dateutil.parser.parse(end_dict["dateTime"]).astimezone(datetime.timezone.utc)
        elif "date" in end_dict:
            d = datetime.date.fromisoformat(end_dict["date"])
            end_time = datetime.datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=datetime.timezone.utc)
        else:
            end_time = start_time + datetime.timedelta(hours=1)

        # Organizer details
        organizer = raw.get("organizer", {})
        organizer_email = organizer.get("email")

        # Attendees
        attendees = raw.get("attendees", [])
        attendees_json = json.dumps([
            {
                "email": a.get("email"),
                "displayName": a.get("displayName"),
                "responseStatus": a.get("responseStatus"),
            }
            for a in attendees if "email" in a
        ]) if attendees else None

        recurrence = json.dumps(raw.get("recurrence")) if raw.get("recurrence") else None

        return {
            "event_id": event_id,
            "calendar_id": calendar_id,
            "summary": summary,
            "description": description,
            "location": location,
            "start_time": start_time,
            "end_time": end_time,
            "is_all_day": is_all_day,
            "status": status,
            "organizer_email": organizer_email,
            "attendees": attendees_json,
            "recurrence": recurrence,
            "html_link": html_link,
        }
