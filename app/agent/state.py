from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Execution state of the LangGraph multi-agent telephone representative."""
    # Caller context
    query: str
    caller_phone: Optional[str]
    call_id: Optional[str]
    chat_history: List[Dict[str, str]]

    # Routing and orchestration
    route: Optional[str]  # "gmail", "calendar", "direct", "safety_block"
    needs_calendar: bool
    needs_gmail: bool

    # Retrieved Evidence Grounding
    retrieved_evidence: List[Dict[str, Any]]
    evidence_valid: bool
    evidence_summary: Optional[str]

    # Safety, policy, and prompt-injection checks
    is_safe: bool
    safety_violations: List[str]
    is_injection_attempt: bool

    # Response generation
    response_text: str
    sources_used: List[Dict[str, str]]
    audit_trail: List[str]
