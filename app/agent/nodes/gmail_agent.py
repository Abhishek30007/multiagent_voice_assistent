import re
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from app.agent.state import AgentState
from app.agent.tools.retrieval_tools import search_gmail_records
from app.core.logger import logger


async def gmail_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Gmail Agent: queries ingested email records in PostgreSQL for relevant facts."""
    query = state.get("query", "")
    audit_trail = list(state.get("audit_trail", []))
    retrieved_evidence = list(state.get("retrieved_evidence", []))

    configurable = config.get("configurable", {})
    session = configurable.get("db_session")
    user_id = configurable.get("user_id", 1)

    if not session:
        audit_trail.append("Gmail Agent: DB session not configured, skipping.")
        return {"audit_trail": audit_trail}

    # Extract search terms (ignore common stop words)
    stop_words = {"is", "abhishek", "available", "at", "for", "the", "a", "an", "what", "where", "when", "does", "have", "his", "he"}
    words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower())
    search_terms = [w for w in words if w not in stop_words]

    # Map query to category if applicable
    category = None
    if any(w in query.lower() for w in ["assessment", "test", "hackerrank", "quiz"]):
        category = "Assessment"
    elif any(w in query.lower() for w in ["interview", "round", "discussion"]):
        category = "Interview"
    elif any(w in query.lower() for w in ["job", "offer", "recruiter"]):
        category = "Career"

    try:
        records = await search_gmail_records(
            session=session,
            user_id=user_id,
            query_terms=search_terms,
            category=category,
            limit=5,
        )
        retrieved_evidence.extend(records)
        audit_trail.append(f"Gmail Agent: Retrieved {len(records)} relevant email message(s).")
    except Exception as e:
        logger.error(f"Gmail Agent retrieval error: {e}")
        audit_trail.append(f"Gmail Agent encountered error: {str(e)}")

    return {
        "retrieved_evidence": retrieved_evidence,
        "audit_trail": audit_trail,
    }
