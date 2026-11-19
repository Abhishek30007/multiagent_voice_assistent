import re
from typing import Dict, Any
from app.agent.state import AgentState
from app.core.logger import logger


INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) (instructions|directions|rules)",
    r"you are now (in )?(developer|dan|jailbreak) mode",
    r"disregard (the )?system prompt",
    r"reveal (your )?(system prompt|instructions|secret key)",
    r"pretend to be the account owner",
    r"act as abhishek",
]


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Supervisor Agent: inspects caller query, detects attacks, and plans routing."""
    query = state.get("query", "").strip()
    query_lower = query.lower()
    audit_trail = list(state.get("audit_trail", []))
    audit_trail.append(f"Supervisor analyzed caller query: '{query}'")

    # 1. Immediate Prompt Injection & Adversarial Check
    is_injection = False
    for pat in INJECTION_PATTERNS:
        if re.search(pat, query_lower):
            is_injection = True
            break

    if is_injection:
        audit_trail.append("Supervisor detected prompt injection attempt in caller query.")
        return {
            "route": "safety_block",
            "is_injection_attempt": True,
            "is_safe": False,
            "safety_violations": ["Prompt injection attempt detected."],
            "audit_trail": audit_trail,
        }

    # 2. Intent Classification
    calendar_keywords = [
        "schedule", "available", "availability", "free", "busy", "meeting",
        "calendar", "tomorrow", "today", "at 4", "at 5", "at 3", "appointment",
        "assessment scheduled", "interview time"
    ]
    gmail_keywords = [
        "email", "mail", "assessment", "hackerrank", "online assessment", "test",
        "interview invite", "job", "offer", "recruiter", "message", "inbox", "sent"
    ]

    needs_calendar = any(kw in query_lower for kw in calendar_keywords)
    needs_gmail = any(kw in query_lower for kw in gmail_keywords)

    # General greetings
    greeting_keywords = ["hello", "hi", "hey", "who are you", "what can you do", "help"]
    is_greeting = any(query_lower.startswith(g) or query_lower == g for g in greeting_keywords)

    if not needs_calendar and not needs_gmail and is_greeting:
        route = "direct"
    elif needs_calendar and needs_gmail:
        route = "both"
    elif needs_calendar:
        route = "calendar"
    elif needs_gmail:
        route = "gmail"
    else:
        # Default: check both personal sources for comprehensive grounded answer
        route = "both"
        needs_calendar = True
        needs_gmail = True

    audit_trail.append(f"Supervisor route decision: route={route}, needs_calendar={needs_calendar}, needs_gmail={needs_gmail}")

    return {
        "route": route,
        "needs_calendar": needs_calendar,
        "needs_gmail": needs_gmail,
        "is_injection_attempt": False,
        "audit_trail": audit_trail,
    }
