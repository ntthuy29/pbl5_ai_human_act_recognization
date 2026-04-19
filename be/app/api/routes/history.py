from fastapi import APIRouter, Query

from app.services.history_service import history_service

router = APIRouter()


@router.get("/history")
def get_history(limit: int = Query(default=100, ge=1, le=500)):
	return {
		"success": True,
		"data": history_service.get_all(limit=limit),
	}
