from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_or_create_owner_user
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.common import APIResponse
from app.agent.graph import personal_ai_graph
from app.core.logger import logger

router = APIRouter()


@router.post("/query", response_model=APIResponse[AgentQueryResponse], summary="Query LangGraph Multi-Agent System")
async def query_agent(
    payload: AgentQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute LangGraph multi-agent telephone reasoning flow."""
    user = await get_or_create_owner_user(db)

    initial_state = {
        "query": payload.query,
        "caller_phone": payload.caller_phone,
        "call_id": payload.call_id,
        "chat_history": payload.chat_history or [],
        "route": None,
        "needs_calendar": False,
        "needs_gmail": False,
        "retrieved_evidence": [],
        "evidence_valid": False,
        "evidence_summary": None,
        "is_safe": True,
        "safety_violations": [],
        "is_injection_attempt": False,
        "response_text": "",
        "sources_used": [],
        "audit_trail": [f"Session started for caller '{payload.caller_phone or 'Anonymous'}'."],
    }

    try:
        config = {
            "configurable": {
                "db_session": db,
                "user_id": user.id,
            }
        }
        final_state = await personal_ai_graph.ainvoke(initial_state, config=config)

        return APIResponse(
            success=True,
            data=AgentQueryResponse(
                query=payload.query,
                response_text=final_state.get("response_text", ""),
                is_safe=final_state.get("is_safe", True),
                evidence_valid=final_state.get("evidence_valid", False),
                sources_used=final_state.get("sources_used", []),
                audit_trail=final_state.get("audit_trail", []),
            ),
        )
    except Exception as e:
        logger.error(f"LangGraph agent execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {str(e)}",
        )


@router.get("/topology", summary="Get LangGraph Multi-Agent Topology")
async def get_agent_topology():
    """Returns the nodes and architecture of the multi-agent system."""
    return {
        "nodes": [
            {"id": "supervisor", "name": "Supervisor Agent", "role": "Intent Classification & Attack Neutralization"},
            {"id": "gmail_agent", "name": "Gmail Retrieval Agent", "role": "Email Ground-Truth Evidence Extraction"},
            {"id": "calendar_agent", "name": "Calendar Agent", "role": "Schedule & Free/Busy Calculation"},
            {"id": "evidence_validator", "name": "Evidence Validation Agent", "role": "Anti-Hallucination & Grounding Check"},
            {"id": "safety_agent", "name": "Safety & Policy Agent", "role": "Privacy, Permissions & Disclosure Control"},
            {"id": "response_agent", "name": "Response Generation Agent", "role": "Voice-Optimized Persona Formulator"},
        ],
        "sources": ["Gmail (Primary)", "Google Calendar (Primary)"],
    }
