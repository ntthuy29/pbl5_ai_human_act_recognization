from fastapi import APIRouter
from typing import List

from app.core.app_state import app_state

router = APIRouter()


@router.get("/raw_samples")
def get_raw_samples(limit: int = 20):
    """Return the most recent raw CSI samples collected by the backend.

    `limit` controls how many latest samples to return (default 20).
    """
    try:
        data: List[List[float]] = list(app_state.recent_raw_samples)[-int(limit) :]
    except Exception:
        data = []

    return {"success": True, "data": data}
