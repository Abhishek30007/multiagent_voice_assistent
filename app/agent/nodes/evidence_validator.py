from typing import Dict, Any, List
from app.agent.state import AgentState


def evidence_validation_node(state: AgentState) -> Dict[str, Any]:
    """Evidence Validation Agent: validates retrieved evidence and prevents hallucination."""
    query = state.get("query", "").strip().lower()
    evidence = state.get("retrieved_evidence", [])
    route = state.get("route", "")
    audit_trail = list(state.get("audit_trail", []))

    # If it's a general greeting or identity query, no personal evidence is needed
    general_queries = ["hello", "hi", "hey", "who are you", "what do you do", "help"]
    if any(query.startswith(g) or query == g for g in general_queries):
        audit_trail.append("Evidence Validator: General query requires no personal evidence.")
        return {
            "evidence_valid": True,
            "evidence_summary": "General conversational query. No personal record lookup required.",
            "sources_used": [],
            "audit_trail": audit_trail,
        }

    sources_used = []
    summary_parts = []

    for item in evidence:
        src_type = item.get("source_type")
        if src_type == "calendar":
            summary_parts.append(
                f"[Calendar Event] '{item.get('summary')}' from {item.get('start_time')} to {item.get('end_time')} (Status: {item.get('status')})"
            )
            sources_used.append({
                "type": "calendar",
                "id": str(item.get("id")),
                "title": str(item.get("summary")),
            })
        elif src_type == "email":
            summary_parts.append(
                f"[Email Message] Subject: '{item.get('subject')}' from {item.get('sender')} on {item.get('date')} (Category: {item.get('category')}): {item.get('snippet')}"
            )
            sources_used.append({
                "type": "email",
                "id": str(item.get("id")),
                "title": str(item.get("subject")),
            })

    if not summary_parts:
        # No evidence found in connected personal sources
        audit_trail.append("Evidence Validator: No verified evidence found matching the query. Flagging invalid evidence.")
        return {
            "evidence_valid": False,
            "evidence_summary": None,
            "sources_used": [],
            "audit_trail": audit_trail,
        }

    audit_trail.append(f"Evidence Validator: Validated {len(sources_used)} grounded evidence source(s).")
    return {
        "evidence_valid": True,
        "evidence_summary": "\n".join(summary_parts),
        "sources_used": sources_used,
        "audit_trail": audit_trail,
    }
