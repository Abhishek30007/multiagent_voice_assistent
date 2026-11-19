import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc

from app.core.database import get_db
from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventOut, AvailabilityResponse
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.v1.endpoints.auth import get_or_create_owner_user

router = APIRouter()


@router.get("/events", response_model=PaginatedResponse[CalendarEventOut], summary="List Calendar Events")
async def list_calendar_events(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    time_min: Optional[datetime.datetime] = Query(None, description="Filter events ending after this time"),
    time_max: Optional[datetime.datetime] = Query(None, description="Filter events starting before this time"),
    search: Optional[str] = Query(None, description="Search term in summary or description"),
    status_filter: Optional[str] = Query(None, description="Filter by status (confirmed, tentative, cancelled)"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve calendar events with time-range filtering."""
    user = await get_or_create_owner_user(db)
    query = select(CalendarEvent).where(CalendarEvent.user_id == user.id)

    if time_min:
        query = query.where(CalendarEvent.end_time >= time_min)
    if time_max:
        query = query.where(CalendarEvent.start_time <= time_max)
    if status_filter:
        query = query.where(CalendarEvent.status == status_filter)
    if search:
        search_filter = or_(
            CalendarEvent.summary.ilike(f"%{search}%"),
            CalendarEvent.description.ilike(f"%{search}%"),
            CalendarEvent.location.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    query = query.order_by(asc(CalendarEvent.start_time))

    result = await db.execute(query)
    all_events = result.scalars().all()
    total = len(all_events)

    # In-memory slice for simplicity
    start_idx = (page - 1) * limit
    paginated_items = all_events[start_idx : start_idx + limit]
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedResponse(
        items=[CalendarEventOut.model_validate(e) for e in paginated_items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/availability", response_model=APIResponse[AvailabilityResponse], summary="Check Schedule Availability")
async def check_availability(
    start_time: datetime.datetime = Query(..., description="Target slot start time (UTC or with timezone)"),
    end_time: datetime.datetime = Query(..., description="Target slot end time (UTC or with timezone)"),
    db: AsyncSession = Depends(get_db),
):
    """Check if the user has any conflicting events in a given time window."""
    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be strictly after start_time",
        )

    user = await get_or_create_owner_user(db)

    # An event conflicts if event.start_time < target_end AND event.end_time > target_start
    # and status is not 'cancelled'
    query = select(CalendarEvent).where(
        and_(
            CalendarEvent.user_id == user.id,
            CalendarEvent.status != "cancelled",
            CalendarEvent.start_time < end_time,
            CalendarEvent.end_time > start_time,
        )
    ).order_by(asc(CalendarEvent.start_time))

    result = await db.execute(query)
    conflicts = result.scalars().all()

    is_available = len(conflicts) == 0

    return APIResponse(
        success=True,
        message="Available" if is_available else f"Busy with {len(conflicts)} conflicting event(s)",
        data=AvailabilityResponse(
            target_start=start_time,
            target_end=end_time,
            is_available=is_available,
            conflicts=[CalendarEventOut.model_validate(c) for c in conflicts],
        ),
    )


@router.get("/events/{event_id}", response_model=APIResponse[CalendarEventOut], summary="Get Event by ID")
async def get_event_detail(event_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch details of a specific calendar event."""
    user = await get_or_create_owner_user(db)
    result = await db.execute(
        select(CalendarEvent).where(
            and_(CalendarEvent.id == event_id, CalendarEvent.user_id == user.id)
        )
    )
    event_record = result.scalars().first()
    if not event_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with ID {event_id} not found",
        )

    return APIResponse(
        success=True,
        data=CalendarEventOut.model_validate(event_record),
    )
