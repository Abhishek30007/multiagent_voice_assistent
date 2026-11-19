import base64
import datetime
import email.utils
import re
from typing import List, Dict, Any, Optional, Tuple
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.logger import logger


class GmailClient:
    """Client for querying the Google Gmail REST API."""

    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the user's Gmail profile containing email address and latest historyId."""
        return self.service.users().getProfile(userId="me").execute()

    def list_message_ids(
        self,
        query: Optional[str] = None,
        max_results: int = 100,
        page_token: Optional[str] = None,
    ) -> Tuple[List[str], Optional[str]]:
        """List message IDs matching the given query."""
        params: Dict[str, Any] = {
            "userId": "me",
            "maxResults": min(max_results, 500),
            "includeSpamTrash": False,
        }
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token

        response = self.service.users().messages().list(**params).execute()
        messages = response.get("messages", [])
        next_page_token = response.get("nextPageToken")
        message_ids = [m["id"] for m in messages if "id" in m]
        return message_ids, next_page_token

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Retrieve full details of an email by message ID."""
        return self.service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

    def get_history(self, start_history_id: str) -> Tuple[List[str], str]:
        """Retrieve message IDs modified or added since start_history_id (incremental sync)."""
        params = {
            "userId": "me",
            "startHistoryId": start_history_id,
            "historyTypes": ["messageAdded"],
        }
        try:
            response = self.service.users().history().list(**params).execute()
            history = response.get("history", [])
            latest_history_id = response.get("historyId", start_history_id)
            
            added_msg_ids = set()
            for record in history:
                for msg_added in record.get("messagesAdded", []):
                    msg = msg_added.get("message")
                    if msg and "id" in msg:
                        added_msg_ids.add(msg["id"])
            return list(added_msg_ids), str(latest_history_id)
        except Exception as e:
            logger.warning(f"Failed to fetch Gmail history (token may be outdated): {e}")
            raise

    @staticmethod
    def parse_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Extract a header value case-insensitively."""
        name_lower = name.lower()
        for h in headers:
            if h.get("name", "").lower() == name_lower:
                return h.get("value")
        return None

    @classmethod
    def parse_email_payload(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw Gmail API response into clean structured dictionary."""
        msg_id = raw.get("id")
        thread_id = raw.get("threadId")
        snippet = raw.get("snippet", "")
        labels = raw.get("labelIds", [])
        internal_date_ms = raw.get("internalDate")

        payload = raw.get("payload", {})
        headers = payload.get("headers", [])

        subject = cls.parse_header(headers, "Subject") or "(No Subject)"
        from_header = cls.parse_header(headers, "From") or ""
        to_header = cls.parse_header(headers, "To") or ""
        cc_header = cls.parse_header(headers, "Cc")
        bcc_header = cls.parse_header(headers, "Bcc")
        date_header = cls.parse_header(headers, "Date")

        # Parse sender name and email
        sender_name, sender_email = email.utils.parseaddr(from_header)
        if not sender_email and from_header:
            sender_email = from_header

        # Parse received date
        received_at: datetime.datetime
        if date_header:
            try:
                parsed_date = email.utils.parsedate_to_datetime(date_header)
                received_at = parsed_date.astimezone(datetime.timezone.utc)
            except Exception:
                if internal_date_ms:
                    received_at = datetime.datetime.fromtimestamp(
                        int(internal_date_ms) / 1000.0, tz=datetime.timezone.utc
                    )
                else:
                    received_at = datetime.datetime.now(datetime.timezone.utc)
        elif internal_date_ms:
            received_at = datetime.datetime.fromtimestamp(
                int(internal_date_ms) / 1000.0, tz=datetime.timezone.utc
            )
        else:
            received_at = datetime.datetime.now(datetime.timezone.utc)

        # Extract body (plain text and html) and attachment presence
        body_text, body_html, has_attachments = cls._extract_body_and_attachments(payload)
        
        # If body_text is empty but body_html exists, strip HTML tags to form text
        if not body_text and body_html:
            clean = re.sub(r"<style.*?</style>", "", body_html, flags=re.DOTALL)
            clean = re.sub(r"<script.*?</script>", "", clean, flags=re.DOTALL)
            clean = re.sub(r"<[^>]+>", " ", clean)
            body_text = re.sub(r"\s+", " ", clean).strip()

        # Categorize email based on content and subject
        category = cls._categorize_email(subject, body_text or snippet)

        is_unread = "UNREAD" in labels

        return {
            "message_id": msg_id,
            "thread_id": thread_id,
            "sender_name": sender_name or None,
            "sender_email": sender_email or "unknown@domain.com",
            "recipient": to_header,
            "cc": cc_header,
            "bcc": bcc_header,
            "subject": subject,
            "snippet": snippet,
            "body_text": body_text,
            "body_html": body_html,
            "received_at": received_at,
            "labels": ",".join(labels) if labels else None,
            "category": category,
            "is_read": not is_unread,
            "has_attachments": has_attachments,
        }

    @classmethod
    def _extract_body_and_attachments(cls, payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], bool]:
        """Walk MIME structure recursively to extract body text and check attachments."""
        body_text_parts: List[str] = []
        body_html_parts: List[str] = []
        has_attachments = False

        def walk_parts(part: Dict[str, Any]):
            nonlocal has_attachments
            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")
            body = part.get("body", {})
            data = body.get("data")

            if filename:
                has_attachments = True

            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8", errors="replace")
                    if mime_type == "text/plain":
                        body_text_parts.append(decoded)
                    elif mime_type == "text/html":
                        body_html_parts.append(decoded)
                except Exception as e:
                    logger.debug(f"Failed to decode part data: {e}")

            for subpart in part.get("parts", []):
                walk_parts(subpart)

        walk_parts(payload)

        plain_text = "\n".join(body_text_parts).strip() if body_text_parts else None
        html_text = "\n".join(body_html_parts).strip() if body_html_parts else None
        return plain_text, html_text, has_attachments

    @staticmethod
    def _categorize_email(subject: str, text: str) -> str:
        """Classify email for quick query routing."""
        combined = f"{subject} {text}".lower()

        if re.search(r"\b(assessment|exam|test|hackerrank|leetcode|codeforces|quiz|online test|proctor)\b", combined):
            return "Assessment"
        if re.search(r"\b(interview|round|technical round|hr round|discussion|invitation to interview)\b", combined):
            return "Interview"
        if re.search(r"\b(offer letter|internship|job|career|application status|shortlisted|recruiter)\b", combined):
            return "Career"
        if re.search(r"\b(invoice|receipt|billing|bank|payment|statement|credit card|debited)\b", combined):
            return "Finance"
        if re.search(r"\b(security alert|verification code|otp|password reset|verify your email)\b", combined):
            return "Security"
        if re.search(r"\b(meeting|zoom|google meet|teams|agenda|discussion|sync)\b", combined):
            return "Meeting"
        if re.search(r"\b(newsletter|digest|promotion|unsubscribe|weekly update)\b", combined):
            return "Newsletter"

        return "General"
