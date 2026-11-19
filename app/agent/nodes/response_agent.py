import os
from typing import Dict, Any
from app.agent.state import AgentState
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()


def generate_gemini_voice_response(query: str, evidence_summary: str, api_key: str) -> str:
    """Use Gemini 2.5 Flash to synthesize natural grounded spoken response."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = f"""You are Abhishek's AI telephone assistant. A caller is speaking to you.
He is currently unavailable.
Your role: Answer the caller politely, naturally, and concisely (1-2 short spoken sentences).

CRITICAL GROUNDING RULES:
1. ONLY state facts that are explicitly provided in the verified evidence below.
2. NEVER invent or assume any personal details, dates, or commitments.
3. If the evidence does not answer the question, say: "I don't have verified information about that in Abhishek's schedule or messages. I can take a message for him."
4. Do not pretend to be Abhishek. Always maintain the AI assistant persona.

VERIFIED EVIDENCE:
{evidence_summary}

CALLER QUESTION:
"{query}"

CONCISE SPOKEN RESPONSE:"""

        for model_name in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as model_err:
                continue
    except Exception as e:
        logger.warning(f"Gemini API call failed, falling back to deterministic response: {e}")
    return ""


def response_agent_node(state: AgentState) -> Dict[str, Any]:
    """Response Agent: converts validated facts into a concise, polite voice response."""
    query = state.get("query", "").strip()
    query_lower = query.lower()
    is_safe = state.get("is_safe", True)
    safety_violations = state.get("safety_violations", [])
    evidence_valid = state.get("evidence_valid", False)
    evidence_summary = state.get("evidence_summary")
    audit_trail = list(state.get("audit_trail", []))

    # 1. Safety or Policy Block
    if not is_safe:
        reason = safety_violations[0] if safety_violations else "Policy restriction"
        audit_trail.append(f"Response Agent: Generating safety refusal for: {reason}")
        if "modify" in reason.lower() or "action" in reason.lower():
            response_text = "I cannot modify Abhishek's calendar or send emails directly. I can take a message and ask him to review your request."
        else:
            response_text = "I cannot share that confidential information over the phone. I can take a message for Abhishek if you'd like."
        return {
            "response_text": response_text,
            "audit_trail": audit_trail,
        }

    # 2. General Greeting / Identity
    greeting_keywords = ["hello", "hi", "hey", "who are you", "what can you do", "help"]
    if any(query_lower.startswith(g) or query_lower == g for g in greeting_keywords):
        audit_trail.append("Response Agent: Delivering standard AI introduction greeting.")
        return {
            "response_text": "Hello, I'm Abhishek's AI assistant. He is currently unavailable. How may I help you today?",
            "audit_trail": audit_trail,
        }

    # 3. Grounded Abstention (No verified evidence in Gmail or Calendar)
    if not evidence_valid or not evidence_summary:
        audit_trail.append("Response Agent: Abstaining due to lack of verified personal evidence.")
        return {
            "response_text": "I don't have verified information about that in Abhishek's schedule or messages. I can take a message for him.",
            "audit_trail": audit_trail,
        }

    # 4. Try Gemini LLM Generation if API key is present
    gemini_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if gemini_key and not gemini_key.startswith("your-"):
        llm_response = generate_gemini_voice_response(query, evidence_summary, gemini_key)
        if llm_response:
            audit_trail.append("Response Agent: Grounded response synthesized via Gemini LLM.")
            return {
                "response_text": llm_response,
                "audit_trail": audit_trail,
            }

    # 5. Deterministic Grounded Template Fallback
    calendar_items = [e for e in state.get("retrieved_evidence", []) if e.get("source_type") == "calendar"]
    email_items = [e for e in state.get("retrieved_evidence", []) if e.get("source_type") == "email"]

    if any(kw in query_lower for kw in ["available", "free", "busy", "schedule", "tomorrow", "assessment scheduled"]):
        if calendar_items:
            first_evt = calendar_items[0]
            summary = first_evt.get("summary", "an event")
            response_text = f"I checked his schedule. Abhishek has '{summary}' scheduled around that time, so he may be unavailable."
        elif email_items:
            first_mail = email_items[0]
            response_text = f"According to his emails regarding '{first_mail.get('subject')}', there is a scheduled assessment."
        else:
            response_text = "According to his calendar, Abhishek appears to be free during that time."
    elif calendar_items:
        first_evt = calendar_items[0]
        summary = first_evt.get("summary", "an event")
        response_text = f"According to his calendar, Abhishek has '{summary}' scheduled."
    elif email_items:
        first_mail = email_items[0]
        subj = first_mail.get("subject", "an email")
        response_text = f"I found an email regarding '{subj}' from {first_mail.get('sender')}. Would you like me to note a follow-up for Abhishek?"
    else:
        response_text = "Based on his verified records, Abhishek has upcoming commitments. May I take a message for him?"

    audit_trail.append(f"Response Agent: Grounded response generated successfully.")
    return {
        "response_text": response_text,
        "audit_trail": audit_trail,
    }
