import datetime
import re
from typing import Dict, Any, Tuple, Optional
from langchain_core.runnables import RunnableConfig
from app.agent.state import AgentState
from app.agent.tools.retrieval_tools import search_calendar_records
from app.core.database import AsyncSessionLocal
from app.core.logger import logger


def parse_time_window_from_query(query: str) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """Resolve temporal references in caller query to UTC start and end bounds."""
    now = datetime.datetime.now(datetime.timezone.utc)
    query_lower = query.lower()

    has_date_keyword = False
    target_date = now.date()
    if "tomorrow" in query_lower:
        target_date = target_date + datetime.timedelta(days=1)
        has_date_keyword = True
    elif "yesterday" in query_lower:
        target_date = target_date - datetime.timedelta(days=1)
        has_date_keyword = True
    elif "today" in query_lower:
        has_date_keyword = True

    # Check for specific hour mention like "4 pm", "16:00", "4:00 pm"
    hour_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", query_lower)
    if hour_match:
        hour = int(hour_match.group(1))
        minute = int(hour_match.group(2) or 0)
        meridiem = hour_match.group(3)

        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

        target_dt = datetime.datetime(
            target_date.year, target_date.month, target_date.day,
            hour, minute, 0, tzinfo=datetime.timezone.utc
        )
        # Search window from 1 hour before to 1 hour after
        return target_dt - datetime.timedelta(hours=1), target_dt + datetime.timedelta(hours=2)

    if has_date_keyword:
        # Search the entire target day
        start_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=datetime.timezone.utc)
        return start_dt, end_dt

    # If no specific day is mentioned (e.g. "When is his interview?"), search forward 90 days
    return now - datetime.timedelta(days=1), now + datetime.timedelta(days=90)


async def calendar_agent_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Calendar Agent: queries stored calendar events in PostgreSQL for schedule facts."""
    query = state.get("query", "")
    audit_trail = list(state.get("audit_trail", []))
    retrieved_evidence = list(state.get("retrieved_evidence", []))

    configurable = config.get("configurable", {})
    session = configurable.get("db_session")
    user_id = configurable.get("user_id", 1)

    start_window, end_window = parse_time_window_from_query(query)

    words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query.lower())
    stop_words = {"is", "abhishek", "available", "at", "for", "the", "a", "an", "tomorrow", "today", "schedule", "free", "busy"}
    query_terms = [w for w in words if w not in stop_words]

    async def _query_with_session(s):
        return await search_calendar_records(
            session=s,
            user_id=user_id,
            start_time=start_window,
            end_time=end_window,
            query_terms=query_terms if query_terms else None,
            limit=5,
        )

    try:
        if session:
            records = await _query_with_session(session)
        else:
            async with AsyncSessionLocal() as fallback_s:
                records = await _query_with_session(fallback_s)

        retrieved_evidence.extend(records)
        audit_trail.append(f"Calendar Agent: Retrieved {len(records)} relevant calendar event(s).")
    except Exception as e:
        logger.error(f"Calendar Agent retrieval error: {e}")
        audit_trail.append(f"Calendar Agent encountered error: {str(e)}")

    return {
        "retrieved_evidence": retrieved_evidence,
        "audit_trail": audit_trail,
    }
