from fastapi import APIRouter
from app.core.telemetry import metrics_collector
from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/dashboard", response_model=APIResponse[dict], summary="Get System Observability Metrics")
async def get_dashboard_metrics():
    """Retrieve performance, latency, token consumption, and error rates."""
    summary = metrics_collector.get_summary()
    return APIResponse(
        success=True,
        message="Observability metrics retrieved",
        data=summary,
    )
