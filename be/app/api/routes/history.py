from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.history_service import history_service

router = APIRouter()


@router.get("/history")
def get_history(
    limit: int = Query(default=100, ge=1, le=500),
    user: User = Depends(get_current_user),
):
	return {
		"success": True,
		"data": history_service.get_all(limit=limit, user_id=user.id),
	}
