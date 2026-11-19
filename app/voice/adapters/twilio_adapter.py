from typing import Dict, Any
from fastapi.responses import Response
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()


class TwilioVoiceAdapter:
    """Handles Twilio Voice webhooks, TwiML generation, and media streams."""

    @staticmethod
    def generate_twiml_greeting(message: str) -> str:
        """Generate TwiML response to greet the caller."""
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">{message}</Say>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="/api/v1/voice/twilio/process_speech" method="POST">
        <Say voice="Polly.Aditi">How may I help you today?</Say>
    </Gather>
    <Say voice="Polly.Aditi">I did not hear any question. Please feel free to call back. Goodbye!</Say>
</Response>"""
        return twiml

    @staticmethod
    def generate_twiml_response(response_text: str) -> str:
        """Generate follow-up TwiML turn."""
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">{response_text}</Say>
    <Gather input="speech" timeout="5" speechTimeout="auto" action="/api/v1/voice/twilio/process_speech" method="POST">
        <Say voice="Polly.Aditi">Is there anything else I can help you with?</Say>
    </Gather>
    <Say voice="Polly.Aditi">Thank you for calling Abhishek's AI assistant. Goodbye!</Say>
</Response>"""
        return twiml
