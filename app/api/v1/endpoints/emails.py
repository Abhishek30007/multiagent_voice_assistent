import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc

from app.core.database import get_db
from app.models.email import EmailMessage
from app.models.user import User
from app.schemas.email import EmailMessageOut, EmailStatsOut
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.v1.endpoints.auth import get_or_create_owner_user

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EmailMessageOut], summary="List Ingested Emails")
async def list_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Assessment, Interview, Career)"),
    search: Optional[str] = Query(None, description="Keyword search in subject, sender, or snippet"),
    sender: Optional[str] = Query(None, description="Filter by sender email or name"),
    start_date: Optional[datetime.datetime] = Query(None, description="Filter received_at on or after"),
    end_date: Optional[datetime.datetime] = Query(None, description="Filter received_at on or before"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve ingested emails with rich filtering and pagination."""
    user = await get_or_create_owner_user(db)
    query = select(EmailMessage).where(EmailMessage.user_id == user.id)

    if category:
        query = query.where(func.lower(EmailMessage.category) == category.lower())

    if sender:
        query = query.where(
            or_(
                EmailMessage.sender_email.ilike(f"%{sender}%"),
                EmailMessage.sender_name.ilike(f"%{sender}%"),
            )
        )

    if search:
        search_filter = or_(
            EmailMessage.subject.ilike(f"%{search}%"),
            EmailMessage.snippet.ilike(f"%{search}%"),
            EmailMessage.sender_name.ilike(f"%{search}%"),
            EmailMessage.sender_email.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)

    if start_date:
        query = query.where(EmailMessage.received_at >= start_date)

    if end_date:
        query = query.where(EmailMessage.received_at <= end_date)

    # Count total matching
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Pagination and order
    query = query.order_by(desc(EmailMessage.received_at))
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    emails = result.scalars().all()

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedResponse(
        items=[EmailMessageOut.model_validate(e) for e in emails],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/stats/summary", response_model=APIResponse[EmailStatsOut], summary="Get Email Ingestion Statistics")
async def get_email_stats(db: AsyncSession = Depends(get_db)):
    """Summary of ingested emails: total count, categories, and date range."""
    user = await get_or_create_owner_user(db)
    
    total_query = select(func.count(EmailMessage.id)).where(EmailMessage.user_id == user.id)
    total_res = await db.execute(total_query)
    total = total_res.scalar_one()

    category_query = (
        select(EmailMessage.category, func.count(EmailMessage.id))
        .where(EmailMessage.user_id == user.id)
        .group_by(EmailMessage.category)
    )
    cat_res = await db.execute(category_query)
    categories = {cat or "Uncategorized": count for cat, count in cat_res.all()}

    dates_query = select(
        func.min(EmailMessage.received_at),
        func.max(EmailMessage.received_at),
    ).where(EmailMessage.user_id == user.id)
    dates_res = await db.execute(dates_query)
    earliest, latest = dates_res.one()

    return APIResponse(
        success=True,
        data=EmailStatsOut(
            total_emails=total,
            categories=categories,
            earliest_email=earliest,
            latest_email=latest,
        ),
    )


@router.get("/{email_id}", response_model=APIResponse[EmailMessageOut], summary="Get Email by ID")
async def get_email_detail(email_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch details of a specific email by primary key."""
    user = await get_or_create_owner_user(db)
    result = await db.execute(
        select(EmailMessage).where(
            and_(EmailMessage.id == email_id, EmailMessage.user_id == user.id)
        )
    )
    email_record = result.scalars().first()
    if not email_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email with ID {email_id} not found",
        )

    return APIResponse(
        success=True,
        data=EmailMessageOut.model_validate(email_record),
    )
