"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"], tags=["System"])
async def health_check():
    """Basic health probe — always returns 200 if the API is running."""
    from api.main import get_pipeline

    pipeline = get_pipeline()
    if pipeline is None:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "timestamp": datetime.now().isoformat()},
        )
    return pipeline.health_check()
