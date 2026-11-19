import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.call_log import CallLog
from app.api.v1.endpoints.auth import get_or_create_owner_user
from app.schemas.common import APIResponse, PaginatedResponse

router = APIRouter()


class CallLogOut(BaseModel):
    id: int
    call_id: str
    caller_number: str
    call_start_time: str
    duration_seconds: int
    call_status: str
    turn_count: int
    agent_execution_summary: Optional[str] = None
    evidence_sources: List[dict] = []


@router.get("/history", response_model=PaginatedResponse[CallLogOut], summary="List Call History")
async def list_call_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve call logs for the personal AI twin dashboard."""
    user = await get_or_create_owner_user(db)
    query = select(CallLog).where(CallLog.user_id == user.id)

    total_query = select(func.count(CallLog.id)).where(CallLog.user_id == user.id)
    total_res = await db.execute(total_query)
    total = total_res.scalar_one()

    query = query.order_by(desc(CallLog.call_start_time)).offset((page - 1) * limit).limit(limit)
    res = await db.execute(query)
    calls = res.scalars().all()

    items = []
    for c in calls:
        sources = []
        if c.evidence_source_references:
            try:
                sources = json.loads(c.evidence_source_references)
            except Exception:
                sources = []

        items.append(
            CallLogOut(
                id=c.id,
                call_id=c.call_id,
                caller_number=c.caller_number,
                call_start_time=c.call_start_time.isoformat(),
                duration_seconds=c.duration_seconds,
                call_status=c.call_status,
                turn_count=c.turn_count,
                agent_execution_summary=c.agent_execution_summary,
                evidence_sources=sources,
            )
        )

    total_pages = (total + limit - 1) // limit if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )
