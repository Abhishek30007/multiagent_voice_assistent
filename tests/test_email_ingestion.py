import base64
import datetime
import pytest
from app.services.google.gmail_service import GmailClient


def test_categorize_email():
    assert GmailClient._categorize_email("HackerRank Assessment Invite", "Please complete test") == "Assessment"
    assert GmailClient._categorize_email("Interview with Google", "Scheduled for tomorrow at 4 PM") == "Interview"
    assert GmailClient._categorize_email("Job Application Update", "Your application has been received") == "Career"
    assert GmailClient._categorize_email("Monthly Bank Statement", "Your balance statement is ready") == "Finance"
    assert GmailClient._categorize_email("Google Verification Code", "Your OTP is 123456") == "Security"
    assert GmailClient._categorize_email("Team sync", "Let us discuss the roadmap") == "Meeting"
    assert GmailClient._categorize_email("Random subject", "Just saying hello") == "General"


def test_parse_email_payload():
    body_text_plain = "Hello Abhishek, your online assessment is scheduled for tomorrow at 4 PM."
    encoded_body = base64.urlsafe_b64encode(body_text_plain.encode("utf-8")).decode("ASCII")

    raw_payload = {
        "id": "18c123456789abc",
        "threadId": "18c123456789abc_thread",
        "snippet": "Hello Abhishek, your online assessment is scheduled...",
        "labelIds": ["INBOX", "UNREAD"],
        "internalDate": "1700000000000",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Invitation to Online Assessment - Software Engineer"},
                {"name": "From", "value": "Hiring Team <recruiter@techcorp.com>"},
                {"name": "To", "value": "abhishekkumarsaw414@gmail.com"},
                {"name": "Date", "value": "Thu, 15 Nov 2026 10:00:00 +0000"},
            ],
            "mimeType": "text/plain",
            "body": {
                "data": encoded_body,
            },
            "parts": [],
        },
    }

    parsed = GmailClient.parse_email_payload(raw_payload)

    assert parsed["message_id"] == "18c123456789abc"
    assert parsed["thread_id"] == "18c123456789abc_thread"
    assert parsed["sender_name"] == "Hiring Team"
    assert parsed["sender_email"] == "recruiter@techcorp.com"
    assert parsed["subject"] == "Invitation to Online Assessment - Software Engineer"
    assert parsed["category"] == "Assessment"
    assert "online assessment is scheduled" in parsed["body_text"]
    assert parsed["is_read"] is False  # Because UNREAD is in labelIds
    assert parsed["has_attachments"] is False
    assert parsed["received_at"].year == 2026
