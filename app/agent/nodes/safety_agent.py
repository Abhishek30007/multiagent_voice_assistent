import re
from typing import Dict, Any, List
from app.agent.state import AgentState

RESTRICTED_QUERY_PATTERNS = [
    (r"\b(password|otp|pin|passcode|token|auth code|secret)\b", "Disclosing security credentials/passwords over the phone is prohibited."),
    (r"\b(bank balance|credit card|cvv|account balance|salary|tax return)\b", "Disclosing confidential financial information is prohibited."),
    (r"\b(send (an )?email|cancel (the )?meeting|delete (the )?event|reschedule (the )?event)\b", "The AI representative cannot perform write actions or modify calendar/emails on behalf of Abhishek."),
    (r"\b(commit|sign|agree to contract)\b", "The AI representative cannot make legally binding commitments."),
]

INDIRECT_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"system prompt override",
    r"exfiltrate data",
    r"reveal confidential",
]


def safety_agent_node(state: AgentState) -> Dict[str, Any]:
    """Safety Agent: enforces disclosure policies, blocks write actions, and neutralizes prompt injections."""
    query = state.get("query", "").lower()
    evidence = state.get("retrieved_evidence", [])
    audit_trail = list(state.get("audit_trail", []))
    violations: List[str] = list(state.get("safety_violations", []))

    # 1. Check Caller Request Policy Violations
    for pat, desc in RESTRICTED_QUERY_PATTERNS:
        if re.search(pat, query):
            violations.append(desc)

    # 2. Check for Indirect Prompt Injection inside retrieved personal emails
    for item in evidence:
        content = (item.get("content") or "").lower()
        snippet = (item.get("snippet") or "").lower()
        combined = f"{content} {snippet}"
        for inj in INDIRECT_INJECTION_PATTERNS:
            if re.search(inj, combined):
                violations.append("Suspicious adversarial content detected in email data source.")
                audit_trail.append(f"Safety Agent: Neutralized indirect prompt injection in email {item.get('id')}.")
                break

    is_safe = len(violations) == 0
    if not is_safe:
        audit_trail.append(f"Safety Agent: Safety check failed with violations: {'; '.join(violations)}")
    else:
        audit_trail.append("Safety Agent: Safety checks passed.")

    return {
        "is_safe": is_safe,
        "safety_violations": violations,
        "audit_trail": audit_trail,
    }
